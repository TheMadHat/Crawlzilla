# Scrapy settings for provider project
import asyncio
from provider.middlewares import ProviderCsvWriterMiddleware 

LOG_ENABLED = True
LOG_ENCODING = "utf-8"
LOG_FORMATTER = "scrapy.logformatter.LogFormatter"
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
LOG_DATEFORMAT = "%Y-%m-%d %H:%M:%S"
LOG_STDOUT = False
LOG_LEVEL = "DEBUG"
LOG_FILE = "monitor.log"

EXTENSIONS = {
    'provider.middlewares.ProgressBar': 100,
    'provider.middlewares.ProviderCsvWriterMiddleware': 800,
}

ITEM_PIPELINES = {
    'provider.pipelines.ProviderPipeline': 300,
}

PROGRESS_BAR_ENABLED = True

BOT_NAME = "yahoo_bot"
SPIDER_MODULES = ["provider.spiders"]
NEWSPIDER_MODULE = "provider.spiders"

USER_AGENT = "Yahoo-Internal-SEO/1.1 (Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko 20100101 Firefox/124 +yo/SEO-bot)"

DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
}
ROBOTSTXT_OBEY = True
COOKIES_ENABLED = False

REDIRECT_ENABLED = True
REDIRECT_MAX_TIMES = 5

CONCURRENT_REQUESTS = 500

AUTOTHROTTLE_ENABLED = False
AUTOTHROTTLE_START_DELAY = 0
AUTOTHROTTLE_MAX_DELAY = 30
AUTOTHROTTLE_TARGET_CONCURRENCY = 500
AUTOTHROTTLE_DEBUG = True

HTTPCACHE_ENABLED = False
HTTPCACHE_EXPIRATION_SECS = 7200
HTTPCACHE_DIR = "httpcache"
HTTPCACHE_IGNORE_HTTP_CODES = []
HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

#DOWNLOAD_DELAY = 3
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False