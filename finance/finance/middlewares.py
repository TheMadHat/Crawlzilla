import csv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
from scrapy import signals
from scrapy.exceptions import NotConfigured

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
            TextColumn("Processed: {task.completed}"),
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
               
class FinanceDownloaderMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        return None

    def process_response(self, request, response, spider):
        if 400 <= response.status < 600:  # Check for 4xx and 5xx status codes
            spider.logger.warning(f"Got bad status code {response.status} for URL: {request.url}")
        return response

    def process_exception(self, request, exception, spider):
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)