import os
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy import signals
from scrapy.spiders import Spider
import logging
from datetime import datetime
import psycopg2
from dotenv import load_dotenv

load_dotenv()

class URLSpider(scrapy.Spider):
    name = "discover"
    rules = (
        Rule(LinkExtractor(), callback='parse_item', follow=True),
    )

    def __init__(self, url_limit=None, *args, **kwargs):
        # Initialize other attributes here, but not self.disallowed_subdomains yet
        super(URLSpider, self).__init__(*args, **kwargs)
        self.db_connection = None
        self.db_cursor = None
        self.url_limit = int(url_limit) if url_limit else 0
        self.processed_count = 0
   
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(URLSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        spider.start_urls = spider.settings.get('START_URL')
        spider.allowed_domains = spider.settings.get('ALLOWED_DOMAINS', [])
        spider.disallowed_subdomains = spider.settings.get('DISALLOWED_SUBDOMAINS', [])
        spider.log_startup_settings()  # Call log_startup_settings here
        return spider

    def spider_opened(self, spider):
        self.start_time = datetime.now()
        self.clear_log_file()
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
        print(f"Concurrency Target: {self.settings.get('CONCURRENT_REQUESTS')}")
        print(f"Batch Size: {self.settings.get('BATCH_SIZE')}")
        print("---------------------------------")

    def spider_closed(self, spider, reason):
        if reason == 'finished':
            self.log_completion_stats()
        # Always close database connections
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

    def parse_item(self, response):
        yield {
            'url': response.url,
            'status': response.status,
        }

        self.processed_count += 1
        if self.url_limit and self.processed_count >= self.url_limit:
            self.logger.info("URL limit reached. Stopping spider.")
            self.crawler.engine.close_spider(self, "URL limit reached")