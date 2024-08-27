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

        return default_config, db_config
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

async def batch_insert_links(pool, link_data_batch):
    """Asynchronously inserts a batch of link data into the database."""
    async with pool.acquire() as conn:
        try:
            insert_query = """
            INSERT INTO links (article_id, anchor_text, link_destination)
            VALUES ($1, $2, $3)
            ON CONFLICT (article_id, anchor_text, link_destination) DO NOTHING
            """
            async with conn.transaction():
                await conn.executemany(insert_query, link_data_batch)
        except (Exception, asyncpg.PostgresError) as error:
            error_logger.error(f"Error during batch insert of links: {error}")

@retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3))
async def fetch(session, url):
    """Fetches the content of a webpage with retry logic and 404 handling."""
    try:
        async with session.get(url, timeout=10) as response:
            if response.status == 404:
                error_logger.warning(f"Resource not found (404) for URL: {url}")
                return None
            response.raise_for_status()
            return await response.text()
    except aiohttp.ClientResponseError as e:
        error_logger.error(f"HTTP error for URL {url}: {e}")
        raise
    except asyncio.TimeoutError:
        error_logger.error(f"Timeout error for URL {url}")
        raise
    except Exception as e:
        error_logger.error(f"An unexpected error occurred while fetching {url}: {e}")
        return None

def url_priority(url):
    """Determines the priority of the URL. .html URLs get higher priority."""
    parsed_url = urlparse(url)
    if parsed_url.path.endswith('.html'):
        return 0  # Higher priority
    return 1  # Lower priority

async def format_and_extract_data(url, search_string, pool, request_timeout, crawled_urls, semaphore, article_data_batch, link_data_batch, batch_size, progress, task_id, crawled_queue, include_list, session, pq, urls_inserted):
    """Fetches, extracts, and saves data, adding new links to queues."""

    async with semaphore:
        try:
            logging.info(f"Fetching: {url}")
            content = await fetch(session, url)
            if content is None:
                error_logger.warning(f"Skipping processing for URL {url} due to 404.")
                return

            soup = BeautifulSoup(content, 'html.parser')
            logging.info(f"Fetched and parsed content from {url}")

            caas_body_div = soup.find('div', class_="caas-body")
            if caas_body_div:
                text = caas_body_div.get_text()
                occurrences = len(re.findall(r'\b' + re.escape(search_string.lower()) + r'\b', text.lower()))
                logging.info(f"Occurrences of '{search_string}': {occurrences}")

                sentences_with_links = 0
                sentences_without_links = 0
                sentences = sent_tokenize(text)
                
                # Prepare a temporary list to hold links before we get the article ID
                temp_link_data_batch = []

                for sentence in sentences:
                    if search_string.lower() in sentence.lower():
                        logging.info(f"Sentence with '{search_string}': {sentence}")
                        links_in_sentence = caas_body_div.find_all('a', href=True)
                        if any(sentence in link.parent.get_text() for link in links_in_sentence):
                            sentences_with_links += 1
                            for link in links_in_sentence:
                                if sentence in link.parent.get_text():
                                    anchor_text = link.get_text().strip()
                                    link_destination = link['href']
                                    temp_link_data_batch.append((None, anchor_text, link_destination))  # Placeholder for article ID
                        else:
                            sentences_without_links += 1

                logging.info(f"Sentences with '{search_string}' and links: {sentences_with_links}")
                logging.info(f"Sentences with '{search_string}' and no links: {sentences_without_links}")

                article_data_batch.append((url, occurrences, sentences_without_links, sentences_with_links))
            else:
                logging.warning(f"Could not find 'div' with class 'caas-body' on {url}, skipping parsing.")

            if len(article_data_batch) >= batch_size:
                async with pool.acquire() as conn:
                    async with conn.transaction():
                        for article_data in article_data_batch:
                            insert_query = """
                            INSERT INTO articles (url, occurrences, sentences_without_links, sentences_with_links)
                            VALUES ($1, $2, $3, $4)
                            ON CONFLICT (url) DO NOTHING
                            RETURNING article_id, url
                            """
                            result = await conn.fetch(insert_query, *article_data)
                            if result:
                                article_id = result[0]['article_id']  # Get the article_id from the result
                                logging.info(f"Inserted article with ID {article_id} and data: {article_data}")

                                for i, link_data in enumerate(temp_link_data_batch):
                                    if link_data[0] is None:
                                        temp_link_data_batch[i] = (article_id, link_data[1], link_data[2])  # Update with article ID

                        article_data_batch.clear()
                        logging.info(f"Inserted batch of articles")

                        if temp_link_data_batch:
                            await conn.executemany("""
                            INSERT INTO links (article_id, anchor_text, link_destination)
                            VALUES ($1, $2, $3)
                            ON CONFLICT (article_id, anchor_text, link_destination) DO NOTHING
                            """, temp_link_data_batch)
                            temp_link_data_batch.clear()
                            logging.info(f"Inserted batch of links")

        except Exception as e:
            error_logger.error(f"An unexpected error occurred while processing {url}: {e}")
            error_logger.exception(e)
        finally:
            await crawled_queue.put(1)
            crawled_count = await crawled_queue.get()
            progress.update(task_id, advance=1, description=f"Crawled: {crawled_count} URLs, Queue: {len(pq)}, Inserted: {urls_inserted}")
            logging.info(f"Updated progress for {url}")

async def crawl_urls(start_url, search_string, pool, request_timeout, url_limit, include_list, concurrent_tasks, batch_size, crawled_urls):
    semaphore = asyncio.Semaphore(concurrent_tasks)
    article_data_batch = []
    link_data_batch = []
    crawled_queue = asyncio.Queue()
    urls_inserted = 0

    pq = [(url_priority(url_normalize(start_url)), url_normalize(start_url), 0)]

    async with aiohttp.ClientSession() as session:
        with Progress(
            "[progress.description]{task.description}",
            SpinnerColumn(),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%", style="cyan"),
            TimeRemainingColumn(),
            transient=True,
        ) as progress:
            task = progress.add_task("Crawling", total=url_limit, crawled=0, queue=len(pq), inserted=0)
            tasks = []

            while pq and len(crawled_urls) < url_limit:
                priority, url, depth = heapq.heappop(pq)

                if url not in crawled_urls:
                    task_id = task
                    tasks.append(asyncio.create_task(format_and_extract_data(
                        url, search_string, pool, request_timeout, crawled_urls,
                        semaphore, article_data_batch, link_data_batch, batch_size,
                        progress, task_id, crawled_queue, include_list, session, pq, urls_inserted
                    )))
                    crawled_urls.add(url)
                    progress.update(task_id, advance=0, crawled=len(crawled_urls), queue=len(pq), inserted=urls_inserted)

                    new_links = await get_new_links(url, include_list, session)
                    for link in new_links:
                        normalized_link = url_normalize(link)
                        if normalized_link not in crawled_urls:
                            heapq.heappush(pq, (url_priority(normalized_link), normalized_link, depth + 1))

            await asyncio.gather(*tasks)
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
    start_time = time.time()
    crawled_urls = set()

    try:
        default_config, db_config = get_config()
        logging.info("Configuration loaded successfully")

        dsn = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}"
        logging.info(f"DSN created: {dsn}")

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
        logging.info("Database connection pool established")

        await crawl_urls(start_url, search_string, pool, default_config['request_timeout'],
                         url_limit, include_list, concurrent_tasks, batch_size, crawled_urls)
        logging.info("Crawling completed")

    except asyncpg.PostgresError as e:
        error_logger.error(f"Database error: {type(e).__name__} - {e}")
        error_logger.exception(e)
    except Exception as e:
        error_logger.error(f"Error in main: {type(e).__name__} - {e}")
        error_logger.exception(e)
    finally:
        if pool:
            # Query to find the number of link opportunities before closing the pool
            try:
                async with pool.acquire() as conn:
                    link_opportunities_query = "SELECT COUNT(*) FROM articles WHERE sentences_without_links > 0;"
                    link_opportunities_count = await conn.fetchval(link_opportunities_query)
                    logging.info(f"Total link opportunities found: {link_opportunities_count}")
                    print(f"Total link opportunities found: {link_opportunities_count}")
            except asyncpg.PostgresError as e:
                error_logger.error(f"Database error when fetching link opportunities: {type(e).__name__} - {e}")
                error_logger.exception(e)
            except Exception as e:
                error_logger.error(f"Error when fetching link opportunities: {type(e).__name__} - {e}")
                error_logger.exception(e)
            
            await pool.close()
            logging.info("Database connection pool closed")

        end_time = time.time()
        total_time = end_time - start_time
        logging.info(f"Total time taken: {total_time:.2f} seconds")
        print(f"Total time taken: {total_time:.2f} seconds")

        total_urls_crawled = len(crawled_urls)
        logging.info(f"Total URLs crawled: {total_urls_crawled}")
        print(f"Total URLs crawled: {total_urls_crawled}")

if __name__ == "__main__":
    asyncio.run(main())