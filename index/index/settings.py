import os
from dotenv import load_dotenv

load_dotenv()

LOG_ENABLED = True
LOG_ENCODING = "utf-8"
LOG_FORMATTER = "scrapy.logformatter.LogFormatter"
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
LOG_DATEFORMAT = "%Y-%m-%d %H:%M:%S"
LOG_STDOUT = False
LOG_LEVEL = "DEBUG"
LOG_FILE = "monitor.log"

EXTENSIONS = {
    'index.middlewares.ProgressBar': 100,
}

ITEM_PIPELINES = {
    'index.pipelines.URLPipeline': 300,
}

BOT_NAME = "yahoo_bot"

SPIDER_MODULES = ["index.spiders"]
NEWSPIDER_MODULE = "index.spiders"

DATABASE_CONFIG = {
    'host': os.getenv('HOST'),
    'database': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

ALLOWED_DOMAINS = ['yahoo.com']
DISALLOWED_SUBDOMAINS = ['finance.yahoo.com']
START_URL = "https://www.yahoo.com"
BATCH_SIZE = 1000

MY_JOBDIR = 'home/ubuntu/crawlzilla_v1/index/index/jobs'

PROGRESS_BAR_ENABLED = True

USER_AGENT = "Yahoo-Internal-SEO/1.1 (Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko 20100101 Firefox/124 +yo/SEO-bot)"

DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9",
}
ROBOTSTXT_OBEY = False
COOKIES_ENABLED = False

REDIRECT_ENABLED = True
REDIRECT_MAX_TIMES = 5

CONCURRENT_REQUESTS = 1000

AUTOTHROTTLE_ENABLED = False
AUTOTHROTTLE_START_DELAY = 0
AUTOTHROTTLE_MAX_DELAY = 30
AUTOTHROTTLE_TARGET_CONCURRENCY = 1000
AUTOTHROTTLE_DEBUG = True

HTTPCACHE_ENABLED = False
#HTTPCACHE_EXPIRATION_SECS = 7200
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"
FEED_EXPORT_ENCODING = "utf-8"

#DOWNLOAD_DELAY = 3
#CONCURRENT_REQUESTS_PER_DOMAIN = 16
#CONCURRENT_REQUESTS_PER_IP = 16

# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False