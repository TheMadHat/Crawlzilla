import os
from datetime import datetime, timezone
from itemadapter import ItemAdapter
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

load_dotenv()

def execute_batch(cursor, query, data, page_size=1000):
    for i in range(0, len(data), page_size):
        cursor.executemany(query, data[i:i + page_size])

class URLPipeline:
    def __init__(self, database_config, batch_size=1000):
        self.database_config = database_config
        self.batch_size = batch_size
        self.data = []
        self.db_conn = None
        self.db_cursor = None

    @classmethod
    def from_crawler(cls, crawler):
        database_config = crawler.settings.get('DATABASE_CONFIG')
        return cls(database_config, batch_size=crawler.settings.get('BATCH_SIZE', 1000))

    def open_spider(self, spider):
        try:
            self.db_conn = psycopg2.connect(**self.database_config)
            self.db_cursor = self.db_conn.cursor()
        except psycopg2.Error as e:
            spider.logger.error(f"Error connecting to database: {e}")
            raise  # Consider how you want to handle this error

    def close_spider(self, spider):
        if self.data:
            self.insert_data(spider)
        if self.db_cursor:
            self.db_cursor.close()
        if self.db_conn:
            self.db_conn.close()

    def process_item(self, item, spider):
        timestamp = datetime.now(timezone.utc)
        self.data.append((item['url'], item.get('priority', 1), timestamp))  # Default priority

        if len(self.data) >= self.batch_size:
            self.insert_data(spider)

        return item

    def insert_data(self, spider):
        if not self.data:
            spider.logger.info("No data to insert.")
            return

        try:
            insert_query = sql.SQL("""
                INSERT INTO discovery (url, priority, timestamp)
                VALUES (%s, %s, %s)
                ON CONFLICT (url) DO UPDATE SET
                    priority = EXCLUDED.priority,
                    timestamp = EXCLUDED.timestamp
            """)
            execute_batch(self.db_cursor, insert_query, self.data)
            self.db_conn.commit()
            self.data.clear()
            spider.logger.info(f"Inserted {len(self.data)} records into the database.")
        except psycopg2.Error as e:
            self.db_conn.rollback()
            spider.logger.error(f"Error inserting data: {e}")
            raise  

class IndexPipeline:
    def process_item(self, item, spider):
        return item
