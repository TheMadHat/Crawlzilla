import scrapy
import psycopg2
from scrapy import signals
from urllib.parse import urlparse
from datetime import datetime

from psycopg2.pool import ThreadedConnectionPool

class URLSpider(scrapy.Spider):
    name = "sorter"

    def __init__(self, url_limit=None, *args, **kwargs):
        super(URLSpider, self).__init__(*args, **kwargs)
        self.db_pool = None 
        self.url_limit = int(url_limit) if url_limit else None
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
            self.db_pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=40,  # Adjust as needed
                dbname=self.db_name,
                user=self.db_user,
                password=self.db_password,
                host=self.db_host
            )
            self.logger.info("Successfully connected to the database pool")
            print("Successfully connected to the database pool")
        except psycopg2.Error as e:
            self.logger.error(f"Failed to connect to database: {e}")
            print(f"Failed to connect to database: {e}")
            raise

    def spider_closed(self, spider, reason):
        if reason == 'finished':
            self.log_completion_stats()
        if self.db_pool:
            self.db_pool.closeall()
        self.logger.info(f"Spider closed: {reason}")
        print(f"Spider closed: {reason}")

    def clear_log_file(self):
        log_file = self.settings.get('LOG_FILE', 'monitor.log')
        with open(log_file, 'w') as f:
            f.write('')  # This will clear the file
        self.logger.info(f"Cleared log file: {log_file}")
        print(f"Cleared log file: {log_file}")

    def log_startup_settings(self):
        self.logger.info(f"Disallowed Subdomains: {self.disallowed_subdomains}")
        print(f"Disallowed Subdomains: {self.disallowed_subdomains}")
        self.logger.info(f"Allowed Subdomain: {self.allowed_subdomain}")
        print(f"Allowed Subdomain: {self.allowed_subdomain}")
        self.logger.info(f"Concurrency Target: {self.settings.get('CONCURRENT_REQUESTS')}")
        print(f"Concurrency Target: {self.settings.get('CONCURRENT_REQUESTS')}")
        self.logger.info(f"Batch Size: {self.settings.get('BATCH_SIZE')}")
        print(f"Batch Size: {self.settings.get('BATCH_SIZE')}")
        self.logger.info(f"URL Limit: {self.url_limit if self.url_limit else 'No limit'}")
        print(f"URL Limit: {self.url_limit if self.url_limit else 'No limit'}")

    def log_completion_stats(self):
        elapsed_time = datetime.now() - self.start_time
        stats = self.crawler.stats.get_stats()
        self.logger.info(f"Elapsed Time: {elapsed_time}")
        print(f"Elapsed Time: {elapsed_time}")
        self.logger.info(f"Max Memory Usage: {stats.get('memusage/max')}")
        print(f"Max Memory Usage: {stats.get('memusage/max')}")
        self.logger.info(f"Requests: {stats.get('downloader/request_count', 0)}")
        print(f"Requests: {stats.get('downloader/request_count', 0)}")
        self.logger.info(f"Responses: {stats.get('downloader/response_count', 0)}")
        print(f"Responses: {stats.get('downloader/response_count', 0)}")
        self.logger.info(f"Dupe Filter: {stats.get('dupefilter/filtered', 0)}")
        print(f"Dupe Filter: {stats.get('dupefilter/filtered', 0)}")
        self.logger.info(f"Skipped: {stats.get('httperror/response_ignored_count', 0)}")
        print(f"Skipped: {stats.get('httperror/response_ignored_count', 0)}")
        self.logger.info(f"Processed: {stats.get('item_scraped_count', 0)}")
        print(f"Processed: {stats.get('item_scraped_count', 0)}")

    def start_requests(self):
        chunk_size = 100
        offset = 0
        chunk_counter = 0

        while True:
            chunk_counter += 1
            self.logger.info(f"Fetching chunk {chunk_counter}, offset: {offset}")

            try:
                with self.db_pool.getconn() as self.db_conn:
                    self.logger.info(f"Obtained connection {self.db_conn} from pool in chunk {chunk_counter}")
                    with self.db_conn.cursor() as self.db_cursor:
                        self.db_cursor.execute(f"""
                            SELECT id, url
                            FROM urls
                            WHERE NOT EXISTS (
                                SELECT 1
                                FROM processed_urls
                                WHERE processed_urls.url = urls.url
                            )
                            LIMIT {chunk_size} OFFSET {offset}
                        """)
                        rows = self.db_cursor.fetchall()
                        self.logger.info(f"Fetched {len(rows)} rows in chunk {chunk_counter}")

                self.logger.info(f"Released connection {self.db_conn} after chunk {chunk_counter}")  # Log release

                if not rows:
                    break

                for row in rows:
                    url = row[1]
                    parsed_url = urlparse(url)
                    if parsed_url.hostname is None:
                        self.logger.warning(f"Skipping invalid URL: {url}")
                        continue

                    if not url.startswith('http://') and not url.startswith('https://'):
                        url = 'https://' + url

                    self.logger.info(f"Requesting URL: {url}")
                    yield scrapy.Request(url=url, callback=self.parse, meta={'id': row[0], 'url': url}, dont_filter=True)

                offset += chunk_size

            except psycopg2.Error as e:
                self.logger.error(f"Database query failed: {e}")
                print(f"Database query failed: {e}")
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
                'url': response.meta['url'],
                'provider': provider
            }

        try:
            with self.db_pool.getconn() as self.db_conn:
                with self.db_conn.cursor() as self.db_cursor:                    
                    self.db_cursor.execute(
                        "INSERT INTO processed_urls (url) VALUES (%s)",
                        (response.meta['url'],) 
                    )
                    self.db_conn.commit()
                    self.logger.info(f"Marked URL as processed: {response.meta['url']}")

        except psycopg2.Error as e:
            self.logger.error(f"Failed to update database: {e}")
            print(f"Failed to update database: {e}")    
            if self.db_conn:
                self.db_conn.rollback()

        self.processed_count += 1
        if self.url_limit and self.processed_count >= self.url_limit:
            self.logger.info(f"URL limit of {self.url_limit} reached. Stopping spider.")
            print(f"URL limit of {self.url_limit} reached. Stopping spider.")  
            raise scrapy.exceptions.CloseSpider(reason='url_limit_reached')