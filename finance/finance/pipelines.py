import psycopg2
import os
from psycopg2.extras import execute_batch
from datetime import datetime, timezone
from psycopg2 import sql

class FinancePipeline:
    def __init__(self, db_host, db_name, db_user, db_password, batch_size=250):
        self.db_name = 'provider'
        self.db_user = 'postgres'
        self.db_password = 'JollyRoger123'
        self.db_host = 'localhost'
        self.batch_size = batch_size
        self.processed_ids = []
        self.one_p_data = []
        self.three_p_data = []
        self.db_conn = None
        self.db_cursor = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            db_host='localhost',
            db_name='provider',
            db_user='postgres',
            db_password='JollyRoger123',
            batch_size=crawler.settings.getint('BATCH_SIZE', 250)
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
        data = (item['id'], item['url'], item['provider'], timestamp)
        
        if "Yahoo" in item['provider']:
            self.one_p_data.append(data)
        else:
            self.three_p_data.append(data)

        if len(self.one_p_data) + len(self.three_p_data) >= self.batch_size:
            self.insert_data(spider)

        return item

    def insert_data(self, spider):
        if not self.db_conn or not self.db_cursor:
            spider.logger.error("Database connection or cursor is None")
            return

        if not self.one_p_data and not self.three_p_data:
            spider.logger.info("No data to insert.")
            return

        try:
            # Insert into one_p table
            if self.one_p_data:
                insert_query = sql.SQL("""
                    INSERT INTO one_p (id, url, provider, timestamp)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        url = EXCLUDED.url,
                        provider = EXCLUDED.provider,
                        timestamp = EXCLUDED.timestamp
                """)
                execute_batch(self.db_cursor, insert_query, self.one_p_data)
                spider.logger.info(f"Inserted {len(self.one_p_data)} rows into one_p table.")
                self.one_p_data.clear()

            # Insert into three_p table
            if self.three_p_data:
                insert_query = sql.SQL("""
                    INSERT INTO three_p (id, url, provider, timestamp)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        url = EXCLUDED.url,
                        provider = EXCLUDED.provider,
                        timestamp = EXCLUDED.timestamp
                """)
                execute_batch(self.db_cursor, insert_query, self.three_p_data)
                spider.logger.info(f"Inserted {len(self.three_p_data)} rows into three_p table.")
                self.three_p_data.clear()

            self.db_conn.commit()

        except Exception as e:
            self.db_conn.rollback()
            spider.logger.error(f"Error inserting data: {e}")
            raise e