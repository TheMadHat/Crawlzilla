# pipelines.py
import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime, timezone

class ProviderPipeline:
    def __init__(self, db_host, db_name, db_user, db_password, batch_size=5000):
        self.db_host = db_host
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.batch_size = batch_size
        self.one_p_data = []
        self.three_p_data = []
        self.master_data = []
        self.db_conn = None
        self.db_cursor = None

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            db_host=crawler.settings.get('DB_HOST'),
            db_name=crawler.settings.get('DB_NAME'),
            db_user=crawler.settings.get('DB_USER'),
            db_password=crawler.settings.get('DB_PASSWORD'),
            batch_size=crawler.settings.getint('BATCH_SIZE', 5000)
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
        provider = item.get('provider')
        timestamp = datetime.now(timezone.utc)
        id = item['id']

        if "Yahoo" in provider:
            self.one_p_data.append((id, item['url'], provider, timestamp))
        else:
            self.three_p_data.append((id, item['url'], provider, timestamp))

        if len(self.one_p_data) + len(self.three_p_data) >= self.batch_size:
            self.insert_data(spider)

        return item

    def insert_data(self, spider):
        if not self.db_conn or not self.db_cursor:
            return

        try:
            # Insert into one_p first
            if self.one_p_data:
                execute_batch(
                    self.db_cursor,
                    "INSERT INTO one_p (id, url, provider, timestamp) VALUES (%s, %s, %s, %s)",
                    self.one_p_data
                )
                self.master_data.extend(self.one_p_data)
                self.one_p_data.clear()

            # Insert into three_p next
            if self.three_p_data:
                execute_batch(
                    self.db_cursor,
                    "INSERT INTO three_p (id, url, provider, timestamp) VALUES (%s, %s, %s, %s)",
                    self.three_p_data
                )
                self.master_data.extend(self.three_p_data)
                self.three_p_data.clear()

            self.db_conn.commit()

            # Insert into master last
            if self.master_data:
                execute_batch(
                    self.db_cursor,
                    "INSERT INTO master (id, url, provider, timestamp) VALUES (%s, %s, %s, %s)",
                    self.master_data
                )
                self.master_data.clear()

            self.db_conn.commit()

        except Exception as e:
            self.db_conn.rollback()
            spider.logger.error(f"Error inserting data: {e}")
            raise e
