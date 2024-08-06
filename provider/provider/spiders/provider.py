import scrapy
from scrapy import signals
import psycopg2
from urllib.parse import urlparse
from scrapy.utils.project import get_project_settings

class URLSpider(scrapy.Spider):
    name = "provider"

    def __init__(self, url_limit=None, *args, **kwargs):
        super(URLSpider, self).__init__(*args, **kwargs)
        self.db_connection = None
        self.db_cursor = None
        settings = get_project_settings()
        self.disallowed_subdomains = settings.get('DISALLOWED_SUBDOMAINS', [])
        self.url_limit = int(url_limit) if url_limit else 0
        self.processed_count = 0
        self.total_urls = 0

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(URLSpider, cls).from_crawler(crawler, *args, **kwargs)
        spider.settings = crawler.settings
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_opened(self, spider):
        self.clear_log_file()
        try:
            self.db_connection = psycopg2.connect(
                host=self.settings.get('DB_HOST'),
                database=self.settings.get('DB_NAME'),
                user=self.settings.get('DB_USER'),
                password=self.settings.get('DB_PASSWORD')
            )
            self.db_cursor = self.db_connection.cursor()
            
            # Count total URLs
            self.db_cursor.execute("SELECT COUNT(*) FROM urls")
            self.total_urls = self.db_cursor.fetchone()[0]
            self.logger.info(f"Total URLs in database: {self.total_urls}")
            self.logger.info(f"Disallowed subdomains: {self.disallowed_subdomains}")
            
        except psycopg2.Error as e:
            self.logger.error(f"Failed to connect to database: {e}")
            raise

    def spider_closed(self, spider):
        if self.db_cursor:
            self.db_cursor.close()
        if self.db_connection:
            self.db_connection.close()

    def clear_log_file(self):
        log_file = self.settings.get('LOG_FILE', 'monitor.log')
        with open(log_file, 'w') as f:
            f.write('')
        self.logger.info(f"Cleared log file: {log_file}")

    def is_allowed_url(self, url):
        parsed_url = urlparse(url)
        return all(subdomain not in parsed_url.netloc for subdomain in self.disallowed_subdomains)

    def start_requests(self):
        if not self.db_cursor:
            self.logger.error("Database cursor not initialized")
            return

        try:
            self.db_cursor.execute("SELECT id, url FROM urls")
            rows = self.db_cursor.fetchall()
            allowed_count = 0
            for row in rows:
                if self.url_limit and self.processed_count >= self.url_limit:
                    self.logger.info(f"URL limit reached: {self.url_limit}")
                    break

                url = row[1]
                if self.is_allowed_url(url):
                    allowed_count += 1
                    yield scrapy.Request(url=url, callback=self.parse, meta={'id': row[0]})
                # Removed the else clause that was logging skipped URLs

            self.logger.info(f"Total allowed URLs to crawl: {allowed_count}")

        except psycopg2.Error as e:
            self.logger.error(f"Database query failed: {e}")
            raise

    def parse(self, response):
        provider_texts = response.css('span.caas-attr-provider::text').getall()
        if not provider_texts:
            provider_texts = response.css('a.link.caas-attr-provider::text').getall()

        for text in provider_texts:
            provider = text.strip()
            yield {
                'id': response.meta['id'],
                'url': response.url,
                'provider': provider
            }

        self.processed_count += 1
        if self.url_limit and self.processed_count >= self.url_limit:
            self.logger.info("URL limit reached. Stopping spider.")
            self.crawler.engine.close_spider(self, "URL limit reached")