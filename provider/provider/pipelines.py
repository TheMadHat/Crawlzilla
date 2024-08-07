import psycopg2
import os
from psycopg2.extras import execute_batch
from datetime import datetime, timezone
from psycopg2 import sql

class ProviderPipeline:
    def __init__(self, db_host, db_name, db_user, db_password, batch_size=1000):
        print("ProviderPipeline initialized with batch size:", batch_size)
        self.db_name = os.environ.get('DB_NAME')
        self.db_user = os.environ.get('DB_USER')
        self.db_password = os.environ.get('DB_PASSWORD')
        self.db_host = os.environ.get('DB_HOST')
        self.batch_size = batch_size
        self.data = []
        self.db_conn = None
        self.db_cursor = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            db_host=crawler.settings.get('DB_HOST'),
            db_name=crawler.settings.get('DB_NAME'),
            db_user=crawler.settings.get('DB_USER'),
            db_password=crawler.settings.get('DB_PASSWORD'),
            batch_size=crawler.settings.getint('BATCH_SIZE', 1000)
        )

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
        self.data.append((item['id'], item['url'], item['provider'], timestamp))

        if len(self.data) >= self.batch_size:
            self.insert_data(spider)

        return item

    def insert_data(self, spider):
        if not self.db_conn or not self.db_cursor:
            spider.logger.error("Database connection or cursor is None")
            return

        try:
            # Insert into master table
            insert_query = sql.SQL("""
                INSERT INTO master (id, url, provider, timestamp)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    url = EXCLUDED.url,
                    provider = EXCLUDED.provider,
                    timestamp = EXCLUDED.timestamp
            """)
            execute_batch(self.db_cursor, insert_query, self.data)

            self.db_conn.commit()
            spider.logger.info(f"Inserted {len(self.data)} items into master table")
            self.data.clear()

        except Exception as e:
            self.db_conn.rollback()
            spider.logger.error(f"Error inserting data: {e}")
            raise e