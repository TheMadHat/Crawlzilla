# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html
import csv
from io import StringIO

class ProviderPipeline:
    def __init__(self, batch_size=1000):
        self.csvfile = None
        self.writer = None
        self.buffer = StringIO()
        self.batch_writer = None
        self.batch_size = batch_size
        self.row_count = 0

    def open_spider(self, spider):
        self.csvfile = open("provider_file.csv", "a", newline='')
        self.batch_writer = csv.writer(self.buffer)
        
        # Write header only if the file is empty
        if self.csvfile.tell() == 0:
            csv.writer(self.csvfile).writerow(['url', 'provider'])

    def close_spider(self, spider):
        self._write_buffer()
        if self.csvfile:
            self.csvfile.close()

    def process_item(self, item, spider):
        if 'provider' in item:
            self.batch_writer.writerow([item['url'], item['provider']])
            self.row_count += 1

            if self.row_count >= self.batch_size:
                self._write_buffer()

        return item

    def _write_buffer(self):
        if self.row_count > 0:
            self.csvfile.write(self.buffer.getvalue())
            self.buffer.truncate(0)
            self.buffer.seek(0)
            self.row_count = 0