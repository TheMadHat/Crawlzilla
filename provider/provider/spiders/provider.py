import scrapy
import os
import psycopg2
from scrapy import signals
from scrapy.spiders import Spider
from urllib.parse import urlparse
from scrapy.exceptions import DontCloseSpider
from datetime import datetime

class URLSpider(scrapy.Spider):
    name = "provider"

    def __init__(self, url_limit=None, *args, **kwargs):
        super(URLSpider, self).__init__(*args, **kwargs)
        self.db_connection = None
        self.db_cursor = None
        self.url_limit = int(url_limit) if url_limit else 0
        self.processed_count = 0
        self.db_name = 'provider'
        self.db_user = 'postgres'
        self.db_password = 'JollyRoger123'
        self.db_host = 'localhost'
   
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(URLSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        spider.disallowed_subdomains = spider.settings.get('DISALLOWED_SUBDOMAINS', [])
        spider.allowed_subdomain = spider.settings.get('ALLOWED_SUBDOMAIN', None)
        spider.log_startup_settings()
        return spider

    def spider_opened(self, spider):
        self.start_time = datetime.now()
        self.clear_log_file()
        try:
            self.db_connection = psycopg2.connect(
                dbname='provider',
                user='postgres',
                password='JollyRoger123',
                host='localhost'
            )
            self.db_cursor = self.db_connection.cursor()
        except psycopg2.Error as e:
            self.logger.error(f"Failed to connect to database: {e}")
            raise

    def clear_log_file(self):
        log_file = self.settings.get('LOG_FILE', 'monitor.log')
        with open(log_file, 'w') as f:
            f.write('')  # This will clear the file
        self.logger.info(f"Cleared log file: {log_file}")

    def log_startup_settings(self):
        log_file = self.settings.get('LOG_FILE', 'monitor.log')
        print(f"Cleared log file: {log_file}")
        print(f"Disallowed Subdomains: {self.disallowed_subdomains}")
        print(f"Allowed Subdomain: {self.allowed_subdomain}")
        print(f"Concurrency Target: {self.settings.get('CONCURRENT_REQUESTS')}")
        print(f"Batch Size: {self.settings.get('BATCH_SIZE')}")
        print("---------------------------------")

    def spider_closed(self, spider, reason):
        if reason == 'finished':
            self.log_completion_stats()
        if self.db_cursor:
            self.db_cursor.close()
        if self.db_connection:
            self.db_connection.close()

    def log_completion_stats(self):
        elapsed_time = datetime.now() - self.start_time
        stats = self.crawler.stats.get_stats()
        print(f"Elapsed Time: {elapsed_time}")
        print(f"Max Memory Usage: {stats.get('memusage/max')}")
        print(f"Requests: {stats.get('downloader/request_count', 0)}")
        print(f"Responses: {stats.get('downloader/response_count', 0)}")
        print(f"200: {stats.get('downloader/response_status_count/200', 0)}")
        print(f"301: {stats.get('downloader/response_status_count/301', 0)}")
        print(f"302: {stats.get('downloader/response_status_count/302', 0)}")
        print(f"307: {stats.get('downloader/response_status_count/307', 0)}")
        print(f"403: {stats.get('downloader/response_status_count/403', 0)}")
        print(f"404: {stats.get('downloader/response_status_count/404', 0)}")
        print(f"429: {stats.get('downloader/response_status_count/429', 0)}")
        print(f"500: {stats.get('downloader/response_status_count/500', 0)}")
        print(f"503: {stats.get('downloader/response_status_count/503', 0)}")
        print(f"504: {stats.get('downloader/response_status_count/504', 0)}")
        print(f"999: {stats.get('downloader/response_status_count/999', 0)}")
        print(f"Dupe Filter: {stats.get('dupefilter/filtered', 0)}")
        print(f"Skipped: {stats.get('httperror/response_ignored_count', 0)}")
        print(f"Processed: {stats.get('item_scraped_count', 0)}")

    def start_requests(self):
        if not self.db_cursor:
            self.logger.error("Database cursor not initialized")
            return

        try:
            self.db_cursor.execute("SELECT id, url FROM urls WHERE processed = False AND bad_url = False")  
            rows = self.db_cursor.fetchall()

            for row in rows:
                if self.url_limit and self.processed_count >= self.url_limit:
                    self.logger.info(f"URL limit reached: {self.url_limit}")
                    break

                url = row[1]
                parsed_url = urlparse(url)
                if parsed_url.hostname is None:
                    self.logger.warning(f"Skipping invalid URL: {url}")
                    continue

                disallowed = False
                for subdomain in self.disallowed_subdomains:
                    if parsed_url.hostname == subdomain or parsed_url.hostname.endswith("." + subdomain):
                        disallowed = True
                        break

                if disallowed:
                    self.logger.info(f"Skipping URL due to disallowed subdomain: {url}")
                    continue

                if self.allowed_subdomain and not parsed_url.hostname.endswith("." + self.allowed_subdomain):
                    self.logger.info(f"Skipping URL due to not matching allowed subdomain: {url}")
                    continue

                yield scrapy.Request(url=url, callback=self.parse, meta={'id': row[0]})

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