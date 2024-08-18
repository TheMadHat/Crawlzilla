import scrapy
from scrapy.linkextractors import LinkExtractor
from urllib.parse import urlparse, urlunparse
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv("/home/ubuntu/crawlzilla_v1/index/config.env")

class YahooSpider(scrapy.Spider):
    name = "discover"
    allowed_domains = ['yahoo.com']
    start_urls = [os.getenv("START_URL")]

    def __init__(self, *args, **kwargs):
        super(YahooSpider, self).__init__(*args, **kwargs)
        self.conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("HOST"),
        )
        self.cur = self.conn.cursor()

    def parse(self, response):
        link_extractor = LinkExtractor(allow=r'\.html$')
        links = link_extractor.extract_links(response)

        for link in links:
            url, priority = self.process_url(link.url)
            self.store_in_db(url, priority)
            yield scrapy.Request(link.url, callback=self.parse, priority=priority)

    def process_url(self, url):
        parsed_url = urlparse(url)
        # Strip parameters and fragments
        clean_url = urlunparse(parsed_url._replace(query="", fragment=""))
        priority = self.determine_priority(parsed_url.path)
        if parsed_url.query:
            self.store_parameters(parsed_url.query, clean_url)
        return clean_url, priority

    def determine_priority(self, path):
        if path.endswith('.html'):
            return 0
        depth = path.count('/')
        if depth == 1:
            return 1
        elif depth == 2:
            return 2
        elif depth == 3:
            return 3
        elif depth == 4:
            return 4
        else:
            return 5

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
        self.cur.close()
        self.conn.close()