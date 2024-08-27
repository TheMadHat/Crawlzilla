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

# Initialize counts for queued URLs, warnings, and errors
total_queued_urls = 0
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
            'start_url': config['DEFAULT']['start_url'],
            'domain': config['DEFAULT']['domain'],
            'url_limit': int(config['DEFAULT']['url_limit']),
            'include': config['DEFAULT']['include'].split(','),
            'search_string': config['DEFAULT']['search_string']
        }

        db_config = {
            'database': config['postgresql']['database'],
            'user': config['postgresql']['user'],
            'password': config['postgresql']['password'],
            'host': config['postgresql']['host']
        }

        queue_db_config = {
            'database': config['queue_postgresql']['database'],
            'user': config['queue_postgresql']['user'],
            'password': config['queue_postgresql']['password'],
            'host': config['queue_postgresql']['host']
        }

        return default_config, db_config, queue_db_config
    except KeyError as e:
        error_logger.error(f"Missing configuration key: {e}")
        raise

def is_included(url, include_list):
    """Checks if the URL belongs to an included subdomain."""
    if not url:
        return None
    parsed_url = urlparse(url)
    if any(include in parsed_url.netloc for include in include_list):
        return url_normalize(url)
    return None

async def batch_insert_articles(pool, article_data_batch):
    """Asynchronously inserts a batch of article data into the database."""
    async with pool.acquire() as conn:
        try:
            insert_query = """
            INSERT INTO articles (url, occurrences, sentences_without_links, sentences_with_links)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT (url) DO NOTHING
            """
            async with conn.transaction():
                await conn.executemany(insert_query, article_data_batch)
        except (Exception, asyncpg.PostgresError) as error:
            error_logger.error(f"Error during batch insert of articles: {error}")


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

def url_priority(url):
    """Determines the priority of the URL. .html URLs get higher priority."""
    parsed_url = urlparse(url)
    if parsed_url.path.endswith('.html'):
        return 0  # Higher priority
    return 1  # Lower priority

async def add_urls_to_queue(queue_pool, urls):
    """Adds a batch of URLs to the database queue with deduplication and retry logic."""
    global total_queued_urls
    for url in urls:
        async with queue_pool.acquire() as conn:
            retries = 0
            while retries < 5:
                try:
                    async with conn.transaction():
                        await conn.execute(
                            """
                            INSERT INTO url_queue (url, priority, depth)
                            VALUES ($1, $2, $3)
                            ON CONFLICT (url) DO NOTHING;
                            """,
                            url, url_priority(url), 0
                        )
                    total_queued_urls += 1
                    break  # Exit the retry loop if successful
                except asyncpg.exceptions.DeadlockDetectedError as e:
                    retries += 1
                    wait_time = random.uniform(0.5, 2**retries)  # Exponential backoff
                    logging.warning(f"Deadlock detected while adding URLs to the queue. Retrying in {wait_time:.2f} seconds...")
                    await asyncio.sleep(wait_time)
                except asyncpg.exceptions.UniqueViolationError:
                    logging.debug(f"URL already in queue: {url}")
                    break  # URL already in queue, no need to retry
            
async def get_urls_from_queue(queue_pool, batch_size):
    """Retrieves a batch of URLs from the database queue, prioritizing by priority and status."""
    async with queue_pool.acquire() as conn:
        async with conn.transaction():
            return await conn.fetch(
                """
                SELECT id, url, depth
                FROM url_queue
                WHERE status = 'pending'
                ORDER BY priority ASC, created_at ASC
                LIMIT $1
                FOR UPDATE SKIP LOCKED
                """,
                batch_size
            )

async def update_url_status(queue_pool, url_id, status):
    """Updates the status of a URL in the queue."""
    async with queue_pool.acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                """
                UPDATE url_queue
                SET status = $1, updated_at = NOW()
                WHERE id = $2
                """,
                status,
                url_id
            )

async def format_and_extract_data(pool, queue_pool, url_id, url, depth, search_string, include_list, session, semaphore, article_data_batch, batch_size):
    """Fetches, extracts, and saves data, adding new links to queues."""
    async with semaphore:
        try:
            if '#' in url or '?' in url:
                logging.warning(f"Skipping URL due to presence of # or ?: {url}")
                await update_url_status(queue_pool, url_id, 'crawled')
                return

            #logging.info(f"Fetching: {url}") # Commented out to reduce log verbosity
            content = await fetch(session, url)
            if content is None:
                error_logger.warning(f"Skipping processing for URL {url} due to fetch errors.")
                await update_url_status(queue_pool, url_id, 'crawled')
                return

            soup = BeautifulSoup(content, 'html.parser')
            # logging.info(f"Fetched and parsed content from {url}") # Commented out to reduce log verbosity

            # Remove h1 and h2 tags and their content
            for h1 in soup.find_all('h1'):
                h1.decompose()
            for h2 in soup.find_all('h2'):
                h2.decompose()

            caas_body_div = soup.find('div', class_="caas-body")
            if caas_body_div:  # Article content found
                text = caas_body_div.get_text()
                occurrences = len(re.findall(r'\b' + re.escape(search_string.lower()) + r'\b', text.lower()))
                # logging.info(f"Occurrences of '{search_string}': {occurrences}") # Commented out to reduce log verbosity

                sentences_with_links = 0
                sentences_without_links = 0
                sentences = sent_tokenize(text)

                for sentence in sentences:
                    if search_string.lower() in sentence.lower():
                        # logging.info(f"Sentence with '{search_string}': {sentence}") # Commented out to reduce log verbosity
                        links_in_sentence = [link for link in caas_body_div.find_all('a', href=True) if
                                             sentence in link.parent.get_text()]
                        if links_in_sentence:
                            sentences_with_links += 1
                            for link in links_in_sentence:
                                anchor_text = link.get_text().strip()
                                link_destination = link['href']
                                # logging.info(f"Link found - Anchor text: '{anchor_text}', Destination: '{link_destination}'") # Commented out to reduce log verbosity
                        else:
                            sentences_without_links += 1

                logging.info(f"Sentences with '{search_string}' and links: {sentences_with_links}")
                logging.info(f"Sentences with '{search_string}' and no links: {sentences_without_links}")

                article_data_batch.append((url, occurrences, sentences_without_links, sentences_with_links))

                if len(article_data_batch) >= batch_size:
                    await batch_insert_articles(pool, article_data_batch)
                    article_data_batch.clear()

            else:
                logging.warning(f"Could not find 'div' with class 'caas-body' on {url}, skipping parsing.")
                # Do not process links if no article content was found
                await update_url_status(queue_pool, url_id, 'crawled') 

            await update_url_status(queue_pool, url_id, 'crawled')
            new_links = await get_new_links(url, include_list, session)
            await add_urls_to_queue(queue_pool, new_links)

        except Exception as e:
            error_logger.error(f"An unexpected error occurred while processing {url}: {e}")
            error_logger.exception(e)
            await update_url_status(queue_pool, url_id, 'error')

async def crawl_urls(start_url, search_string, pool, queue_pool, request_timeout, url_limit, include_list, concurrent_tasks, batch_size):
    """Crawls URLs, managing the queue in the PostgreSQL database."""
    semaphore = asyncio.Semaphore(concurrent_tasks)
    article_data_batch = []
    total_crawled_urls = 0

    async with aiohttp.ClientSession() as session:
        # Add the start URL to the queue initially
        await add_urls_to_queue(queue_pool, [start_url])

        with Progress(
                "[progress.description]{task.description}",
                SpinnerColumn(),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%", style="cyan"),
                TimeRemainingColumn(),
                transient=True,
        ) as progress:
            task = progress.add_task("Crawling", total=url_limit, crawled=0)
            crawled_count = 0
            while crawled_count < url_limit:
                db_urls = await get_urls_from_queue(queue_pool, batch_size)

                if not db_urls:
                    await asyncio.sleep(1)  # Wait for new URLs to be added to the queue
                    continue

                tasks = []
                for record in db_urls:
                    url_id, url, depth = record['id'], record['url'], record['depth']
                    tasks.append(asyncio.create_task(format_and_extract_data(
                        pool, queue_pool, url_id, url, depth, search_string, include_list, session, semaphore,
                        article_data_batch, batch_size
                    )))

                await asyncio.gather(*tasks)
                crawled_count += len(db_urls)
                total_crawled_urls += 1
                progress.update(task, advance=len(db_urls), description=f"Crawled: {crawled_count} URLs")
            logging.info("All tasks gathered and completed")

async def get_new_links(url, include_list, session):
    """Fetches a webpage and extracts new links from it."""
    new_links = []
    try:
        content = await fetch(session, url)
        if content:
            soup = BeautifulSoup(content, 'html.parser')
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href:
                    absolute_url = urljoin(url, href)
                    stripped_url = is_included(absolute_url, include_list)
                    if stripped_url and stripped_url not in new_links:
                        new_links.append(stripped_url)
    except aiohttp.ClientError as e:
        error_logger.error(f"HTTP error for URL {url}: {e}")
    except Exception as e:
        error_logger.error(f"Error fetching URL {url}: {e}")
    return new_links

async def main():
    logging.info("Starting the crawler")
    pool = None
    queue_pool = None
    start_time = time.time()

    try:
        default_config, db_config, queue_db_config = get_config()
        logging.info("Configuration loaded successfully")

        dsn = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}"
        logging.info(f"DSN created: {dsn}")

        queue_dsn = f"postgresql://{queue_db_config['user']}:{queue_db_config['password']}@{queue_db_config['host']}/{queue_db_config['database']}"
        logging.info(f"Queue DSN created: {queue_dsn}")

        start_url = default_config['start_url']
        url_limit = default_config['url_limit']
        include_list = default_config['include']
        concurrent_tasks = default_config['concurrent_tasks']
        batch_size = default_config['batch_size']
        search_string = default_config['search_string']

        logging.info(f"Start URL from configuration: {start_url}")
        logging.info(f"URL limit from configuration: {url_limit}")
        logging.info(f"Inclusion list from configuration: {include_list}")
        logging.info(f"Concurrent tasks: {concurrent_tasks}")
        logging.info(f"Batch size: {batch_size}")
        logging.info(f"Search string: {search_string}")

        pool = await asyncpg.create_pool(dsn)
        logging.info("{search_string} database connection pool established")
        print(f"{search_string} database connection pool established")
        queue_pool = await asyncpg.create_pool(queue_dsn)
        logging.info("URL queue database connection pool established")
        print(f"URL queue database connection pool established")

        await crawl_urls(start_url, search_string, pool, queue_pool, default_config['request_timeout'],
                         url_limit, include_list, concurrent_tasks, batch_size)
        logging.info("Crawling completed")

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
            # Query to find the number of link opportunities before closing the pool
            try:
                async with pool.acquire() as conn:
                    link_opportunities_query = "SELECT COUNT(*) FROM articles WHERE sentences_without_links > 0;"
                    link_opportunities_count = await conn.fetchval(link_opportunities_query)
                    logging.info(f"Total link opportunities found: {link_opportunities_count}")
            except asyncpg.PostgresError as e:
                error_logger.error(f"Database error when fetching link opportunities: {type(e).__name__} - {e}")
                error_logger.exception(e)
                total_errors += 1
            except Exception as e:
                error_logger.error(f"Error when fetching link opportunities: {type(e).__name__} - {e}")
                error_logger.exception(e)
                total_errors += 1

            await pool.close()
            logging.info("Database connection pool closed")

        if queue_pool:
            await queue_pool.close()
            logging.info("Queue database connection pool closed")

        end_time = time.time()
        total_time = end_time - start_time
        logging.info(f"Total time taken: {total_time:.2f} seconds")
        logging.info(f"Total queued URLs: {total_queued_urls}")
        logging.info(f"Total Warnings: {total_warnings}")
        logging.info(f"Total Errors: {total_errors}")
        print(f"Start URL from configuration: {start_url}")
        print(f"URL limit from configuration: {url_limit}")
        print(f"Inclusion list from configuration: {include_list}")
        print(f"Concurrent tasks: {concurrent_tasks}")
        print(f"Batch size: {batch_size}")
        print(f"Search string: {search_string}")
        print(f"---------------------------------------------")
        print(f"Total time taken: {total_time:.2f} seconds")
        print(f"Total link opportunities found: {link_opportunities_count}")
        print(f"Total queued URLs: {total_queued_urls}")
        print(f"Total Warnings: {total_warnings}")
        print(f"Total Errors: {total_errors}")


if __name__ == "__main__":
    asyncio.run(main())