# provider.py
import scrapy
import csv

class URLSpider(scrapy.Spider):
    name = "provider"
    start_urls = []

    def start_requests(self):
        with open("urls.txt", "r") as f:
            urls = f.read().splitlines()
            for url in urls:
                yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        provider_texts = response.css('span.caas-attr-provider::text').getall()
        if not provider_texts:
            provider_texts = response.css('a.link.caas-attr-provider::text').getall()
        
        if provider_texts:
            for text in provider_texts:
                yield {
                    'url': response.url,
                    'provider': text.strip()
                }
        else:
            yield {
                'url': response.url,
                'provider': 'N/A'
            }

    def __init__(self, *args, **kwargs):
        super(URLSpider, self).__init__(*args, **kwargs)
        with open("monitor.log", "w") as f:
            f.write("")