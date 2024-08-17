import os
import csv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from scrapy import signals
from scrapy.exceptions import NotConfigured
from dotenv import load_dotenv

load_dotenv()

class ProgressBar:
    def __init__(self, crawler):
        self.crawler = crawler
        self.task = None
        self.progress = None
        self.console = Console()
        self.total_urls = 0
        self.processed_urls = 0
        self.concurrent_requests = []

    @classmethod
    def from_crawler(cls, crawler):
        if not crawler.settings.getbool("PROGRESS_BAR_ENABLED", True):
            raise NotConfigured
        
        extension = cls(crawler)
        crawler.signals.connect(extension.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(extension.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(extension.item_scraped, signal=signals.item_scraped)
        crawler.signals.connect(extension.request_scheduled, signal=signals.request_scheduled)
        crawler.signals.connect(extension.response_received, signal=signals.response_received)
        return extension

    def spider_opened(self, spider):
        self.total_urls = len(list(spider.start_requests()))
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TextColumn("Concurrent: {task.fields[concurrent]}"),
            TimeRemainingColumn(),
            console=self.console,
            transient=True,
        )
        self.task = self.progress.add_task("[green]Crawling", total=self.total_urls, concurrent=0)
        self.progress.start()

    def spider_closed(self, spider):
        if self.progress:
            self.progress.stop()
        self.console.print(f"Processed URLs: {self.processed_urls}/{self.total_urls}")
        if self.concurrent_requests:
            avg_concurrent = sum(self.concurrent_requests) / len(self.concurrent_requests)
            self.console.print(f"Average Concurrent Requests: {avg_concurrent:.2f}")

    def item_scraped(self, item, response, spider):
        self.processed_urls += 1
        if self.progress:
            self.progress.update(self.task, advance=1)

    def request_scheduled(self, request, spider):
        concurrent = len(self.crawler.engine.slot.inprogress)
        self.concurrent_requests.append(concurrent)
        if self.progress:
            self.progress.update(self.task, concurrent=concurrent)

    def response_received(self, response, request, spider):
        concurrent = len(self.crawler.engine.slot.inprogress)
        self.concurrent_requests.append(concurrent)
        if self.progress:
            self.progress.update(self.task, concurrent=concurrent)

class DiscoverSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)


class DiscoverDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)