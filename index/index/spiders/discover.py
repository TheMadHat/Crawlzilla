import os
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.spiders import CrawlSpider, Rule
from scrapy import signals
from datetime import datetime
import psycopg2
from dotenv import load_dotenv, dotenv_values

for key in dotenv_values().keys():
    if key in os.environ:
        del os.environ[key]

load_dotenv('/home/ubuntu/crawlzilla_v1/index/config.env')

class URLSpider(scrapy.Spider):
    name = "discover"
    start_urls = [
        os.getenv('START_URL', 'https://www.yahoo.com')
    ]

    def start_requests(self):
        for url in self.start_urls:
            self.logger.info(f"Requesting URL: {url}")
            yield scrapy.Request(url=url, dont_filter=True)
    rules = (
        Rule(LinkExtractor(), callback='parse_item', follow=True),
    )

    def __init__(self, url_limit=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url_limit = int(url_limit) if url_limit else 0
        self.processed_count = 0
        self.start_time = None
        self.db_connection = None
        self.db_cursor = None

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        spider.initialize_settings(crawler.settings)
        return spider

    def initialize_settings(self, settings):
        self.start_urls = os.getenv('START_URL')
        self.allowed_domains = settings.get('ALLOWED_DOMAINS', [])
        self.disallowed_subdomains = settings.get('DISALLOWED_SUBDOMAINS', [])
        self.log_startup_settings()

    def spider_opened(self):
        self.start_time = datetime.now()
        self.clear_log_file()

    def clear_log_file(self):
        log_file = self.settings.get('LOG_FILE', 'monitor.log')
        with open(log_file, 'w') as f:
            f.write('')
        self.logger.info(f"Cleared log file: {log_file}")

    def log_startup_settings(self):
        self.logger.info(f"Startup Settings:\n"
                         f"Disallowed Subdomains: {self.disallowed_subdomains}\n"
                         f"Concurrency Target: {self.settings.get('CONCURRENT_REQUESTS')}\n"
                         f"Batch Size: {self.settings.get('BATCH_SIZE')}")

    def spider_closed(self, reason):
        if reason == 'finished':
            self.log_completion_stats()

        if self.db_cursor:
            self.db_cursor.close()
        if self.db_connection:
            self.db_connection.close()

    def log_completion_stats(self):
        elapsed_time = datetime.now() - self.start_time
        stats = self.crawler.stats.get_stats()
        self.logger.info(f"Elapsed Time: {elapsed_time}")
        for code in [200, 301, 302, 307, 403, 404, 429, 500, 503, 504, 999]:
            self.logger.info(f"{code}: {stats.get(f'downloader/response_status_count/{code}', 0)}")
        self.logger.info(f"Dupe Filter: {stats.get('dupefilter/filtered', 0)}")
        self.logger.info(f"Skipped: {stats.get('httperror/response_ignored_count', 0)}")
        self.logger.info(f"Processed: {stats.get('item_scraped_count', 0)}")

    def parse_item(self, response):
        yield {
            'url': response.url,
            'status': response.status,
        }
        self.processed_count += 1
        if self.url_limit and self.processed_count >= self.url_limit:
            self.logger.info("URL limit reached. Stopping spider.")
            self.crawler.engine.close_spider(self, "URL limit reached")