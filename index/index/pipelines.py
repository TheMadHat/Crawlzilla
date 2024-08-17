import os
from itemadapter import ItemAdapter
import psycopg2
from dotenv import load_dotenv

load_dotenv()

class URLPipeline:
    def __init__(self, batch_size=1000):
        self.db_name = os.environ.get('DB_NAME')
        self.db_user = os.environ.get('DB_USER')
        self.db_password = os.environ.get('DB_PASSWORD')
        self.db_host = os.environ.get('DB_HOST')
        self.batch_size = batch_size
        self.processed_ids = []
        self.data = []
        self.db_conn = None
        self.db_cursor = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(batch_size=crawler.settings.get('BATCH_SIZE', 1000))

    def open_spider(self, spider):
        self.db_conn = psycopg2.connect(
            host=self.db_host,
            database=self.db_name,
            user=self.db_user,
            password=self.db_password,
        )
        self.db_cursor = self.db_conn.cursor()

    def close_spider(self, spider):
        self.insert_data(spider)  # Insert any remaining data
        if self.db_cursor:
            self.db_cursor.close()
        if self.db_conn:
            self.db_conn.close()
    
    def process_item(self, item, spider):
        timestamp = datetime.now(timezone.utc)
        self.data.append((item['url'], item['priority'], timestamp))

        if len(self.data) >= self.batch_size:
            self.insert_data(spider)

        return item

    def insert_data(self, spider):
        if not self.db_conn or not self.db_cursor:
            spider.logger.error("Database connection or cursor is None")
            return

        if not self.data:
            spider.logger.info("No data to insert.")
            return

        if not item['url']:
            spider.logger.warning("Skipping item with invalid or None URL")
            return

        try:
            insert_query = sql.SQL("""
                INSERT INTO discovery (id, url, priority, timestamp)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    url = EXCLUDED.url,
                    timestamp = EXCLUDED.timestamp
            """)
            execute_batch(self.db_cursor, insert_query, self.data)

            self.data.clear()

        except Exception as e:
            self.db_conn.rollback()
            spider.logger.error(f"Error inserting data: {e}")
            raise e

class IndexPipeline:
    def process_item(self, item, spider):
        return item
