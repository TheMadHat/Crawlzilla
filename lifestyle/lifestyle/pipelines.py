import psycopg2
import os
from psycopg2.extras import execute_batch
from datetime import datetime, timezone
from psycopg2 import sql

class LifestylePipeline:
    def __init__(self, db_host, db_name, db_user, db_password, batch_size=250):
        self.db_name = 'lifestyle'
        self.db_user = 'postgres'
        self.db_password = 'JollyRoger123'
        self.db_host = 'localhost'
        self.batch_size = batch_size
        self.processed_ids = []
        self.data = []
        self.db_conn = None
        self.db_cursor = None

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
        self.processed_ids.append(item['id'])  # Add ID to processed IDs list

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

        try:
            # Insert into master table
            insert_query = sql.SQL("""
                INSERT INTO one_p (id, url, provider, timestamp)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE SET
                    url = EXCLUDED.url,
                    provider = EXCLUDED.provider,
                    timestamp = EXCLUDED.timestamp
            """)
            execute_batch(self.db_cursor, insert_query, self.data)
            print(f"Inserted {len(self.data)} rows into the table.")

            # Update processed status in urls table
            for i in range(0, len(self.data), self.batch_size):
                batch_ids = [item[0] for item in self.data[i:i + self.batch_size]]
                update_query = sql.SQL("""
                    UPDATE urls
                    SET processed = TRUE
                    WHERE id IN (SELECT unnest FROM UNNEST(%s))
                """)
                self.db_cursor.execute(update_query, (batch_ids,))
                self.db_conn.commit()
                spider.logger.info(f"Marked {len(batch_ids)} URLs as processed in 'urls' table.")
                print(f"Updated {len(batch_ids)} rows into the table.")

            self.data.clear()

        except Exception as e:
            self.db_conn.rollback()
            spider.logger.error(f"Error inserting data: {e}")
            raise e