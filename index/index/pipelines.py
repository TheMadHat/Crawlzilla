import os
import scrapy
from dotenv import load_dotenv
from itemadapter import ItemAdapter

load_dotenv("/home/ubuntu/crawlzilla_v1/index/config.env")

class IndexPipeline:
    def process_item(self, item, spider):
        return item