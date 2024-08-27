import asyncio
import aiohttp
from bs4 import BeautifulSoup
import logging
import configparser
import asyncpg
from datetime import datetime
from urllib.parse import urlparse, urljoin, urlunparse
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn, SpinnerColumn
from collections import deque
from url_normalize import url_normalize
from tenacity import retry, wait_exponential, stop_after_attempt
from nltk.tokenize import sent_tokenize
import heapq
import re
import time

# Initialize logging
logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler("monitor.log")])
error_logger = logging.getLogger('error')
error_logger.setLevel(logging.ERROR)
error_logger.addHandler(logging.FileHandler('error.log'))

# Initialize counts for warnings and errors
total_warnings = 0
total_errors = 0

# Initialize Rich console
console = Console()

def get_config():
    """Reads configuration details from the config.ini file."""
    config = configparser.ConfigParser()
    config.read('config.ini')

    try:
        default_config = {
            'batch_size': int(config['DEFAULT']['batch_size']),
            'concurrent_tasks': int(config['DEFAULT']['concurrent_tasks']),
            'request_timeout': int(config['DEFAULT']['request_timeout']),
            'max_redirects': int(config['DEFAULT']['max_redirects']),
            'user_agent': config['DEFAULT']['user_agent'],
        }

        db_config = {
            'database': config['postgresql']['database'],
            'user': config['postgresql']['user'],
            'password': config['postgresql']['password'],
            'host': config['postgresql']['host']
        }

        return default_config, db_config
    except KeyError as e:
        error_logger.error(f"Missing configuration key: {e}")
        raise

@retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3))
async def fetch(session, url):
    """Fetches the content of a webpage with retry logic and 404 handling."""
    try:
        async with session.get(url, timeout=10, allow_redirects=True, max_redirects=10) as response:
            if response.status == 404:
                error_logger.warning(f"Resource not found (404) for URL: {url}")
                global total_warnings
                total_warnings += 1
                return None
            response.raise_for_status()
            return await response.text()
    except aiohttp.TooManyRedirects as e:
        error_logger.error(f"Too many redirects for URL {url}: {e}")
        total_warnings += 1
        return None
    except aiohttp.ClientResponseError as e:
        error_logger.error(f"HTTP error for URL {url}: {e}")
        total_errors += 1
        raise
    except asyncio.TimeoutError:
        error_logger.error(f"Timeout error for URL {url}")
        total_errors += 1
        raise
    except Exception as e:
        error_logger.error(f"An unexpected error occurred while fetching {url}: {e}")
        total_errors += 1
        return None

async def get_urls_from_one_p(pool, batch_size):
    """Retrieves a batch of URLs from the 'one_p' table where processed=False."""
    async with pool.acquire() as conn:
        async with conn.transaction():
            return await conn.fetch(
                """
                SELECT id, url
                FROM one_p
                WHERE processed = FALSE
                ORDER BY id ASC
                LIMIT $1
                FOR UPDATE SKIP LOCKED
                """,
                batch_size
            )

async def get_queries(pool):
    """Retrieves all queries from the 'query' table."""
    async with pool.acquire() as conn:
        async with conn.transaction():
            return await conn.fetch(
                """
                SELECT query, landing_page
                FROM query
                """
            )

async def update_one_p_status(pool, url_id):
    """Updates the 'processed' status to True in the 'one_p' table."""
    async with pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                UPDATE one_p
                SET processed = TRUE
                WHERE id = $1
                """,
                url_id
            )

async def insert_match(pool, url, query, count, landing_url):
    """Inserts or updates a match in the 'matches' table."""
    async with pool.acquire() as conn:
        try:
            async with conn.transaction():
                insert_query = """
                INSERT INTO matches (url, query, count, landing_url, timestamp)
                VALUES ($1, $2, $3, $4, NOW())
                ON CONFLICT (url, query) DO UPDATE SET count = matches.count + 1, timestamp = NOW()
                """
                await conn.execute(insert_query, url, query, count, landing_url)
        except (Exception, asyncpg.PostgresError) as error:
            error_logger.error(f"Error during insert or update of matches: {error}")

async def process_url(pool, url, queries, session, semaphore):
    """Processes a single URL, checking for query matches and updating the matches table."""
    async with semaphore:
        try:
            #logging.info(f"Fetching: {url}") # Commented out to reduce log verbosity
            content = await fetch(session, url)
            if content is None:
                error_logger.warning(f"Skipping processing for URL {url} due to fetch errors.")
                return

            for query_data in queries:
                query = query_data['query']
                landing_url = query_data['landing_page']

                if query.lower() in content.lower():
                    logging.info(f"Match found: {url} - {query}")
                    await insert_match(pool, url, query, 1, landing_url)

            #logging.info(f"Processed: {url}") # Commented out to reduce log verbosity
        except Exception as e:
            error_logger.error(f"An unexpected error occurred while processing {url}: {e}")
            error_logger.exception(e)
            total_errors += 1
        finally:
            return

async def main():
    logging.info("Starting the URL processing")
    pool = None
    start_time = time.time()

    try:
        default_config, db_config = get_config()
        logging.info("Configuration loaded successfully")

        dsn = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}"
        logging.info(f"DSN created: {dsn}")

        pool = await asyncpg.create_pool(dsn)
        logging.info("Database connection pool established")

        queries = await get_queries(pool)
        logging.info(f"Retrieved {len(queries)} queries")

        batch_size = default_config['batch_size']
        concurrent_tasks = default_config['concurrent_tasks']
        semaphore = asyncio.Semaphore(concurrent_tasks)

        async with aiohttp.ClientSession() as session:
            with Progress(
                    "[progress.description]{task.description}",
                    SpinnerColumn(),
                    BarColumn(),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%", style="cyan"),
                    TimeRemainingColumn(),
                    transient=True,
            ) as progress:
                task = progress.add_task("Processing", total=100, completed=0) # Replace 100 with a more accurate estimation of the total number of URLs
                while True:
                    db_urls = await get_urls_from_one_p(pool, batch_size)
                    if not db_urls:
                        await asyncio.sleep(1)  # Wait for new URLs to be added
                        continue
                    tasks = []
                    for record in db_urls:
                        url_id, url = record['id'], record['url']
                        tasks.append(asyncio.create_task(process_url(pool, url, queries, session, semaphore)))
                    await asyncio.gather(*tasks)
                    for record in db_urls:
                        url_id = record['id']
                        await update_one_p_status(pool, url_id)
                    progress.update(task, advance=len(db_urls), description=f"Processed: {len(db_urls)} URLs")

    except asyncpg.PostgresError as e:
        error_logger.error(f"Database error: {type(e).__name__} - {e}")
        error_logger.exception(e)
        global total_errors
        total_errors += 1
    except Exception as e:
        error_logger.error(f"Error in main: {type(e).__name__} - {e}")
        error_logger.exception(e)
        total_errors += 1
    finally:
        if pool:
            await pool.close()
            logging.info("Database connection pool closed")

        end_time = time.time()
        total_time = end_time - start_time
        logging.info(f"Total time taken: {total_time:.2f} seconds")
        logging.info(f"Total Warnings: {total_warnings}")
        logging.info(f"Total Errors: {total_errors}")
        print(f"---------------------------------------------")
        print(f"Total time taken: {total_time:.2f} seconds")
        print(f"Total Warnings: {total_warnings}")
        print(f"Total Errors: {total_errors}")

if __name__ == "__main__":
    asyncio.run(main())