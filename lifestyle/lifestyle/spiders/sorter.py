import scrapy
import psycopg2
from scrapy import signals
from urllib.parse import urlparse
from datetime import datetime

class URLSpider(scrapy.Spider):
    name = "sorter"

    def __init__(self, url_limit=None, *args, **kwargs):
        super(URLSpider, self).__init__(*args, **kwargs)
        self.db_connection = None
        self.db_cursor = None
        self.url_limit = int(url_limit) if url_limit else 0
        self.processed_count = 0
        self.db_name = 'lifestyle'
        self.db_user = 'postgres'
        self.db_password = 'JollyRoger123'
        self.db_host = 'localhost'
   
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(URLSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        spider.disallowed_subdomains = spider.settings.get('DISALLOWED_SUBDOMAINS', [])
        spider.allowed_subdomain = spider.settings.get('ALLOWED_SUBDOMAIN', [])
        spider.log_startup_settings()
        return spider

    def spider_opened(self, spider):
        self.start_time = datetime.now()
        self.clear_log_file()
        try:
            self.db_connection = psycopg2.connect(
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
                host=self.db_host
            )
            self.db_cursor = self.db_connection.cursor()
            self.logger.info("Successfully connected to the database")
        except psycopg2.Error as e:
            self.logger.error(f"Failed to connect to database: {e}")
            raise

    def spider_closed(self, spider, reason):
        if reason == 'finished':
            self.log_completion_stats()
        if self.db_cursor:
            self.db_cursor.close()
        if self.db_connection:
            self.db_connection.close()
        self.logger.info(f"Spider closed: {reason}")

    def clear_log_file(self):
        log_file = self.settings.get('LOG_FILE', 'monitor.log')
        with open(log_file, 'w') as f:
            f.write('')  # This will clear the file
        self.logger.info(f"Cleared log file: {log_file}")

    def log_startup_settings(self):
        self.logger.info(f"Disallowed Subdomains: {self.disallowed_subdomains}")
        self.logger.info(f"Allowed Subdomain: {self.allowed_subdomain}")
        self.logger.info(f"Concurrency Target: {self.settings.get('CONCURRENT_REQUESTS')}")
        self.logger.info(f"Batch Size: {self.settings.get('BATCH_SIZE')}")

    def log_completion_stats(self):
        elapsed_time = datetime.now() - self.start_time
        stats = self.crawler.stats.get_stats()
        self.logger.info(f"Elapsed Time: {elapsed_time}")
        self.logger.info(f"Max Memory Usage: {stats.get('memusage/max')}")
        self.logger.info(f"Requests: {stats.get('downloader/request_count', 0)}")
        self.logger.info(f"Responses: {stats.get('downloader/response_count', 0)}")
        self.logger.info(f"Dupe Filter: {stats.get('dupefilter/filtered', 0)}")
        self.logger.info(f"Skipped: {stats.get('httperror/response_ignored_count', 0)}")
        self.logger.info(f"Processed: {stats.get('item_scraped_count', 0)}")

    def start_requests(self):
        try:
            self.logger.info("Starting to fetch URLs from the database")
            self.db_cursor.execute("SELECT COUNT(*) FROM urls WHERE processed = False")
            count = self.db_cursor.fetchone()[0]
            self.logger.info(f"Found {count} unprocessed URLs in the database")

            self.db_cursor.execute("SELECT id, url FROM urls WHERE processed = False")
            rows = self.db_cursor.fetchall()

            if not rows:
                self.logger.warning("No unprocessed URLs found in the database")
                return

            for row in rows:
                url = row[1]
                parsed_url = urlparse(url)
                if parsed_url.hostname is None:
                    self.logger.warning(f"Skipping invalid URL: {url}")
                    continue

                if not url.startswith('http://') and not url.startswith('https://'):
                    url = 'https://' + url

                self.logger.info(f"Requesting URL: {url}")
                yield scrapy.Request(url=url, callback=self.parse, meta={'id': row[0]})

        except psycopg2.Error as e:
            self.logger.error(f"Database query failed: {e}")
            raise

    def parse(self, response):
        self.logger.info(f"Parsing response from {response.url}")
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

        try:
            self.db_cursor.execute(
                "UPDATE urls SET processed = True WHERE id = %s",
                (response.meta['id'],)
            )
            self.db_connection.commit()
            self.logger.info(f"Updated URL with id {response.meta['id']} as processed")
        except psycopg2.Error as e:
            self.logger.error(f"Failed to update urls table: {e}")
            self.db_connection.rollback()

        self.processed_count += 1
        if self.url_limit and self.processed_count >= self.url_limit:
            self.logger.info("URL limit reached. Stopping spider.")
            self.crawler.engine.close_spider(self, "URL limit reached")