# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import csv
from itemadapter import ItemAdapter

class ProviderPipeline:
    def __init__(self):
        self.csvfile = None
        self.writer = None

    def open_spider(self, spider):
        self.csvfile = open("provider_file.csv", "a", newline='')
        self.writer = csv.writer(self.csvfile)
        self.writer.writerow(['url', 'provider'])

    def close_spider(self, spider):
        if self.csvfile:
            self.csvfile.close()

    def process_item(self, item, spider):
        if 'provider' in item:
            self.writer.writerow([item['url'], item['provider']])
        return item
