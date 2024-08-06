import psycopg2
from psycopg2.extras import execute_batch
from datetime import datetime, timezone
from psycopg2 import sql

class ProviderPipeline:
    def __init__(self, db_host, db_name, db_user, db_password, batch_size=5000):
        print("ProviderPipeline initialized with batch size:", batch_size)
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
            batch_size=crawler.settings.getint('BATCH_SIZE', 100)
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
        self.insert_data(spider)  # Insert all accumulated data
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

        self.master_data.append((id, item['url'], provider, timestamp))

        if len(self.one_p_data) + len(self.three_p_data) + len(self.master_data) >= self.batch_size:
            self.insert_data(spider)

        return item

    def insert_data(self, spider):
        spider.logger.debug(f"Inserting data: one_p: {len(self.one_p_data)}, three_p: {len(self.three_p_data)}, master: {len(self.master_data)}")
        if not self.db_conn or not self.db_cursor:
            spider.logger.error("Database connection or cursor is None")
            return

        try:
            # Collect all IDs
            all_ids = set(item[0] for item in self.one_p_data + self.three_p_data + self.master_data)

            # Check which IDs already exist in any table
            self.db_cursor.execute("""
                SELECT id FROM (
                    SELECT id FROM master
                    UNION
                    SELECT id FROM one_p
                    UNION
                    SELECT id FROM three_p
                ) AS combined_tables
                WHERE id = ANY(%s)
            """, (list(all_ids),))
            
            existing_ids = set(row[0] for row in self.db_cursor.fetchall())

            # Filter out existing IDs
            self.one_p_data = [item for item in self.one_p_data if item[0] not in existing_ids]
            self.three_p_data = [item for item in self.three_p_data if item[0] not in existing_ids]
            self.master_data = [item for item in self.master_data if item[0] not in existing_ids]

            # Insert new data into one_p
            if self.one_p_data:
                insert_query = sql.SQL("""
                    INSERT INTO one_p (id, url, provider, timestamp)
                    VALUES (%s, %s, %s, %s)
                """)
                execute_batch(self.db_cursor, insert_query, self.one_p_data)

            # Insert new data into three_p
            if self.three_p_data:
                insert_query = sql.SQL("""
                    INSERT INTO three_p (id, url, provider, timestamp)
                    VALUES (%s, %s, %s, %s)
                """)
                execute_batch(self.db_cursor, insert_query, self.three_p_data)

            # Insert new data into master
            if self.master_data:
                insert_query = sql.SQL("""
                    INSERT INTO master (id, url, provider, timestamp)
                    VALUES (%s, %s, %s, %s)
                """)
                execute_batch(self.db_cursor, insert_query, self.master_data)

            self.db_conn.commit()

            # Clear the data lists
            self.one_p_data.clear()
            self.three_p_data.clear()
            self.master_data.clear()

        except Exception as e:
            self.db_conn.rollback()
            spider.logger.error(f"Error inserting data: {e}")
            raise e