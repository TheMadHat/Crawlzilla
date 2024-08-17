import os
import scrapy

class URLSpider(scrapy.Spider):
    name = "indexer"

    def __init__(self, url_limit=None, *args, **kwargs):
        # Initialize other attributes here, but not self.disallowed_subdomains yet
        super(URLSpider, self).__init__(*args, **kwargs)
        self.db_connection = None
        self.db_cursor = None
        self.url_limit = int(url_limit) if url_limit else 0
        self.processed_count = 0
        self.db_name = os.environ.get('DB_NAME')
        self.db_user = os.environ.get('DB_USER')
        self.db_password = os.environ.get('DB_PASSWORD')
        self.db_host = os.environ.get('DB_HOST')
   
    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(URLSpider, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        spider.disallowed_subdomains = spider.settings.get('DISALLOWED_SUBDOMAINS', [])
        spider.log_startup_settings()  # Call log_startup_settings here
        return spider