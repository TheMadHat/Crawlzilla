import os
import scrapy
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import CloseSpider
from urllib.parse import urlparse, urlunparse
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
from rich.console import Console 

load_dotenv("/home/ubuntu/crawlzilla_v1/index/config.env")

class YahooSpider(scrapy.Spider):
    name = "discover"
    allowed_domains = ['yahoo.com']

    def __init__(self, *args, **kwargs):
        super(YahooSpider, self).__init__(*args, **kwargs)
        self.start_urls = ['https://www.yahoo.com']

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse, dont_filter=True)

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(YahooSpider, cls).from_crawler(crawler, *args, **kwargs)
        spider.setup(crawler.settings)
        return spider

    def setup(self, settings):
        self.total_urls = settings.getint("URL_LIMIT", 1000)
        self.conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("HOST"),
        )
        self.cur = self.conn.cursor()
        self.console = Console()
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TextColumn("Concurrent: {task.fields[concurrent]}"),
            TimeRemainingColumn(),
            console=self.console,
        )
        self.task = self.progress.add_task(
            "[green]Crawling", total=self.total_urls, concurrent=0
        )
        self.progress.start()

    def parse(self, response):
        link_extractor = LinkExtractor(allow_domains=self.allowed_domains)
        links = link_extractor.extract_links(response)

        concurrent = len(self.crawler.engine.slot.scheduler)
        self.progress.update(self.task, advance=1, concurrent=concurrent)

        for link in links:
            url, priority = self.process_url(link.url)
            self.store_in_db(url, priority)
            yield scrapy.Request(url, callback=self.parse, priority=priority)

        if self.progress.tasks[self.task].completed >= self.total_urls:
            raise CloseSpider(reason='URL limit reached')

    def process_url(self, url):
        parsed_url = urlparse(url)
        clean_url = urlunparse(parsed_url._replace(query="", fragment=""))
        priority = self.determine_priority(parsed_url.path)
        if parsed_url.query:
            self.store_parameters(parsed_url.query, clean_url)
        return clean_url, priority

    def determine_priority(self, path):
        depth = path.count('/')
        return min(depth, 5)

    def store_in_db(self, url, priority):
        try:
            self.cur.execute(
                sql.SQL("INSERT INTO discovery (url, priority) VALUES (%s, %s) ON CONFLICT (url) DO NOTHING"),
                (url, priority)
            )
            self.conn.commit()
        except Exception as e:
            self.logger.error(f"Error inserting URL {url}: {e}")
            self.conn.rollback()

    def store_parameters(self, params, url):
        try:
            self.cur.execute(
                sql.SQL("INSERT INTO parameters (parameter, url) VALUES (%s, %s) ON CONFLICT DO NOTHING"),
                (params, url)
            )
            self.conn.commit()
        except Exception as e:
            self.logger.error(f"Error inserting parameters for {url}: {e}")
            self.conn.rollback()

    def close(self, reason):
        self.progress.stop()
        self.cur.close()
        self.conn.close()