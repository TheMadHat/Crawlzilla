import scrapy
from urllib.parse import urlparse, urlunparse
from psycopg2 import pool, IntegrityError
import logging
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

class URLSpider(scrapy.Spider):
    name = "indexer"
    allowed_domains = ["yahoo.com"]
    start_urls = ["https://www.yahoo.com/news/kamala-harris-vp-scorecard-171607828.html"]
    url_limit = 3000

    def __init__(self, *args, **kwargs):
        super(URLSpider, self).__init__(*args, **kwargs)
        self.visited_urls = set()
        self.url_count = 0

        # Clear the log files at the start of each crawl
        open("queue.txt", "w").close()
        open("parameter.txt", "w").close()
        open("errors.log", "w").close()

        # Connection pooling for PostgreSQL
        self.postgres_pool = pool.SimpleConnectionPool(
            1, 20, dbname=os.getenv('DB_NAME', 'indexer'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', '^iwiMXdnXRO1I7y*tVQ1kvxGg'),
            host=os.getenv('DB_HOST', 'localhost')
        )

        if self.postgres_pool:
            self.log("Connection pool created successfully")

    def parse(self, response):
        self.log(f"Parsing URL: {response.url}")
        if self.url_count >= self.url_limit:
            self.log(f"URL limit of {self.url_limit} reached. Stopping crawl.")
            return

        provider_text = response.css('span.caas-attr-provider::text').get()
        if provider_text:
            self.log(f"Provider Text: {provider_text}")
            self.insert_into_db(response.url, provider_text)

        links = response.css('a::attr(href)').getall()
        self.log(f"Found {len(links)} links on {response.url}")
        for link in links:
            absolute_link = response.urljoin(link)
            parsed_link = urlparse(absolute_link)
            if "yahoo.com" not in parsed_link.netloc:
                continue

            query = parsed_link.query
            fragment = parsed_link.fragment
            parameters_and_hashes = self.log_parameters(query, fragment)

            normalized_link = urlunparse(parsed_link._replace(query="", fragment=""))
            if normalized_link not in self.visited_urls and self.url_count < self.url_limit:
                self.visited_urls.add(normalized_link)
                self.url_count += 1
                self.log_url(normalized_link)
                priority = self.get_priority(normalized_link)
                self.log(f"Following link: {normalized_link} with priority {priority}")
                yield scrapy.Request(url=absolute_link, callback=self.parse, priority=priority)

        current_url = response.url
        parsed_current_url = urlparse(current_url)
        query = parsed_current_url.query
        fragment = parsed_current_url.fragment
        self.log_parameters(query, fragment)
        normalized_current_url = urlunparse(parsed_current_url._replace(query="", fragment=""))
        self.log(f"Processed URL: {normalized_current_url}, Count: {self.url_count}")

    def log_parameters(self, query, fragment):
        parameters_and_hashes = ""
        if query or fragment:
            parameters_and_hashes = f"?{query}#{fragment}" if query and fragment else f"?{query}" if query else f"#{fragment}"
            with open("parameter.txt", "a") as f:
                f.write(parameters_and_hashes + "\n")
        return parameters_and_hashes

    def log_url(self, url):
        with open("queue.txt", "a") as f:
            f.write(url + "\n")

    def insert_into_db(self, url, provider_text):
        conn = self.postgres_pool.getconn()
        try:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO provider_data (url, provider_text) VALUES (%s, %s)", (url, provider_text))
                conn.commit()
        except IntegrityError:
            self.log(f"Duplicate URL found, skipping: {url}")
            conn.rollback()
        except Exception as e:
            self.log(f"Failed to insert into database: {e}")
            conn.rollback()
        finally:
            self.postgres_pool.putconn(conn)

    def get_priority(self, url):
        if url.endswith(".html"):
            return 10
        return 0

    def closed(self, reason):
        self.postgres_pool.closeall()
        self.log("Database connections closed.")
