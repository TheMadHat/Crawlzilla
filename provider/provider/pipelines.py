from psycopg2 import pool
from psycopg2.extras import execute_batch
from datetime import datetime, timezone
from psycopg2 import sql

class ProviderPipeline:
    def __init__(self, db_host, db_name, db_user, db_password, min_conn=5, max_conn=20, batch_size=1000):
        self.db_pool = pool.SimpleConnectionPool(
            min_conn,
            max_conn,
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password
        )
        self.batch_size = batch_size
        self.data = []

    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            db_host=crawler.settings.get('DB_HOST'),
            db_name=crawler.settings.get('DB_NAME'),
            db_user=crawler.settings.get('DB_USER'),
            db_password=crawler.settings.get('DB_PASSWORD'),
            min_conn=crawler.settings.getint('DB_MIN_CONN', 5),
            max_conn=crawler.settings.getint('DB_MAX_CONN', 20),
            batch_size=crawler.settings.getint('BATCH_SIZE', 1000)
        )

    def process_item(self, item, spider):
        timestamp = datetime.now(timezone.utc)
        self.data.append((item['id'], item['url'], item['provider'], timestamp))

        if len(self.data) >= self.batch_size:
            self.insert_data(spider)

        return item

    def insert_data(self, spider):
        conn = self.db_pool.getconn()
        try:
            with conn.cursor() as cur:
                insert_query = sql.SQL("""
                    INSERT INTO master (id, url, provider, timestamp)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (id) DO UPDATE SET
                        url = EXCLUDED.url,
                        provider = EXCLUDED.provider,
                        timestamp = EXCLUDED.timestamp
                """)
                execute_batch(cur, insert_query, self.data)
            conn.commit()
            spider.logger.info(f"Inserted {len(self.data)} items into master table")
            self.data.clear()
        except Exception as e:
            conn.rollback()
            spider.logger.error(f"Error inserting data: {e}")
            raise e
        finally:
            self.db_pool.putconn(conn)

    def close_spider(self, spider):
        if self.data:
            self.insert_data(spider)
        self.db_pool.closeall()