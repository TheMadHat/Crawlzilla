import psycopg2
import os
from psycopg2.extras import execute_batch
from datetime import datetime, timezone
from psycopg2 import sql
from psycopg2.pool import ThreadedConnectionPool

class LifestylePipeline:
    def __init__(self, db_host, db_name, db_user, db_password, batch_size=250):
        self.db_name = 'lifestyle'
        self.db_user = 'postgres'
        self.db_password = 'JollyRoger123'
        self.db_host = 'localhost'
        self.batch_size = batch_size
        self.processed_ids = []
        self.one_p_data = []
        self.three_p_data = []
        self.db_pool = None  # This will hold the connection pool

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            db_host='localhost',
            db_name='lifestlye',
            db_user='postgres',
            db_password='JollyRoger123',
            batch_size=crawler.settings.getint('BATCH_SIZE', 250)
        )

    def open_spider(self, spider):
        try:
            self.db_pool = ThreadedConnectionPool(
                minconn=1,
                maxconn=10,  # Adjust based on your needs and resources
                host=self.db_host,
                database=self.db_name,
                user=self.db_user,
                password=self.db_password
            )
        except psycopg2.Error as e:
            spider.logger.error(f"Failed to create database connection pool: {e}")
            raise

    def close_spider(self, spider):
        self.insert_data(spider)  # Insert any remaining data
        if self.db_pool:
            self.db_pool.closeall()

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
        if not self.db_pool:
            spider.logger.error("Database connection pool is not initialized.")
            return

        try:
            with self.db_pool.getconn() as self.db_conn:
                self.logger.info("Obtained connection from pool in insert_data")
                print("Obtained connection from pool in insert_data")
                with self.db_conn.cursor() as self.db_cursor:
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
            if self.db_conn:
               self.db_conn.rollback()
            spider.logger.error(f"Error inserting data: {e}")  # Access logger through spider
            print(f"Error inserting data: {e}")
            raise