# provider.py
import scrapy
from scrapy import signals
import psycopg2
from urllib.parse import urlparse

class URLSpider(scrapy.Spider):
    name = "provider"

    def __init__(self, disallowed_subdomains=None, url_limit=None, db_name=None, db_user=None, db_password=None, db_host=None, *args, **kwargs):
        super(URLSpider, self).__init__(*args, **kwargs)
        self.db_connection = None
        self.db_cursor = None
        self.disallowed_subdomains = disallowed_subdomains if disallowed_subdomains else []
        self.url_limit = url_limit if url_limit else 0
        self.processed_count = 0
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.db_host = db_host
        self.crawler = None  # Initialize crawler attribute

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        settings = crawler.settings
        disallowed_subdomains = settings.get('DISALLOWED_SUBDOMAINS', [])
        url_limit = settings.getint('URL_LIMIT', 0)
        db_name = settings.get('DB_NAME')
        db_user = settings.get('DB_USER')
        db_password = settings.get('DB_PASSWORD')
        db_host = settings.get('DB_HOST')
        spider = cls(
            disallowed_subdomains=disallowed_subdomains,
            url_limit=url_limit,
            db_name=db_name,
            db_user=db_user,
            db_password=db_password,
            db_host=db_host,
            *args, **kwargs
        )
        spider.crawler = crawler  # Set the crawler attribute
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_opened(self, spider):
        try:
            self.db_connection = psycopg2.connect(
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
                host=self.db_host
            )
            self.db_cursor = self.db_connection.cursor()
        except psycopg2.Error as e:
            self.logger.error(f"Failed to connect to database: {e}")
            self.crawler.engine.close_spider(self, f"Failed to connect to database: {e}")

    def spider_closed(self, spider):
        if self.db_cursor:
            self.db_cursor.close()
        if self.db_connection:
            self.db_connection.close()

    def start_requests(self):
        if not self.db_cursor:
            self.logger.error("Database cursor not initialized")
            return

        try:
            self.db_cursor.execute("SELECT id, url FROM urls")
            rows = self.db_cursor.fetchall()
            for row in rows:
                if self.url_limit and self.processed_count >= self.url_limit:
                    self.logger.info(f"URL limit reached: {self.url_limit}")
                    break

                url = row[1]
                parsed_url = urlparse(url)
                if parsed_url.hostname in self.disallowed_subdomains:
                    self.logger.info(f"Skipping URL due to disallowed subdomain: {url}")
                    continue

                yield scrapy.Request(url=url, callback=self.parse, meta={'id': row[0]})
        except psycopg2.Error as e:
            self.logger.error(f"Database query failed: {e}")
            self.crawler.engine.close_spider(self, f"Database query failed: {e}")

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
            self.crawler.engine.close_spider(self, "URL limit reached")