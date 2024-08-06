from scrapy import signals
from scrapy.exceptions import NotConfigured
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn

class ProgressBar:
    def __init__(self, crawler):
        self.crawler = crawler
        self.task = None
        self.progress = None
        self.processed_urls = 0
        self.total_urls = 0

    @classmethod
    def from_crawler(cls, crawler):
        if not crawler.settings.getbool("PROGRESS_BAR_ENABLED", True):
            raise NotConfigured
        
        extension = cls(crawler)
        crawler.signals.connect(extension.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(extension.spider_closed, signal=signals.spider_closed)
        crawler.signals.connect(extension.item_scraped, signal=signals.item_scraped)
        return extension

    def spider_opened(self, spider):
        self.total_urls = getattr(spider, 'total_urls', 0)
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeRemainingColumn(),
            refresh_per_second=1  # Limit refresh rate
        )
        self.task = self.progress.add_task("[green]Crawling", total=self.total_urls)
        self.progress.start()

    def spider_closed(self, spider):
        if self.progress:
            self.progress.stop()
        print(f"\nProcessed URLs: {self.processed_urls}/{self.total_urls}")

    def item_scraped(self, item, response, spider):
        self.processed_urls += 1
        if self.progress and self.task:
            self.progress.update(self.task, completed=self.processed_urls)
               
class ProviderCsvWriterMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        middleware = cls()
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(middleware.spider_closed, signal=signals.spider_closed)
        return middleware

    def spider_opened(self, spider):
        self.csvfile = open("provider_file.csv", "a", newline='')
        self.writer = csv.writer(self.csvfile)
        self.writer.writerow(['url', 'provider'])  # Write header row

    def spider_closed(self, spider):
        self.csvfile.close()

    def process_spider_output(self, response, result, spider):
        for item in result:
            if isinstance(item, dict) and 'provider' in item:
                self.writer.writerow([item['url'], item['provider']])
        return result  # Return result AFTER writing to CSV 

class ProviderDownloaderMiddleware:
    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        return None

    def process_response(self, request, response, spider):
        return response

    def process_exception(self, request, exception, spider):
        pass

    def spider_opened(self, spider):
        spider.logger.info("Spider opened: %s" % spider.name)