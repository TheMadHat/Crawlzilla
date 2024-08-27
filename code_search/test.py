import asyncio
import aiohttp
from bs4 import BeautifulSoup
import logging
import configparser
import asyncpg
from urllib.parse import urlparse, urljoin, urlunparse
from collections import deque
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from url_normalize import url_normalize
from tenacity import retry, wait_exponential, stop_after_attempt
import json

# Initialize logging
logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler("monitor.log")])
error_logger = logging.getLogger('error')
error_logger.setLevel(logging.ERROR)
error_logger.addHandler(logging.FileHandler('error.log'))

# Initialize Rich console and progress bar
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
            'include': config['DEFAULT']['include'].split(',')
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
    parsed_url = urlparse(url)
    stripped_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, '', '', ''))
    if any(parsed_url.netloc.endswith(include) for include in include_list):
        return stripped_url
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

async def get_last_inserted_article_id(conn):
    """Retrieves the ID of the last inserted article from the database."""
    try:
        query = "SELECT article_id FROM articles ORDER BY article_id DESC LIMIT 1"
        row = await conn.fetchrow(query)
        return row['article_id'] if row else None 
    except (Exception, asyncpg.PostgresError) as error:
        error_logger.error(f"Error retrieving last inserted article_id: {error}")

@retry(wait=wait_exponential(min=1, max=10), stop=stop_after_attempt(3))
async def fetch(session, url):
    async with session.get(url) as response:
        response.raise_for_status()  # Raise an exception for HTTP errors
        return await response.text()

async def format_and_extract_data(url, search_string, conn, request_timeout, crawled_urls, semaphore, article_data_batch, link_data_batch, batch_size, progress, task_id, crawled_queue, inserted_queue, include_list):
    """Fetches, extracts, and saves data, adding new links to queues."""
    async with semaphore:
        try:
            console.log(f"Fetching: {url}")
            async with aiohttp.ClientSession() as session:
                content = await fetch(session, url)
                soup = BeautifulSoup(content, 'html.parser')
                console.log(f"Fetched and parsed content from {url}")

                # Extract data
                occurrences = content.lower().count(search_string.lower())
                sentences_with_links = [link.get_text(strip=True) for link in soup.find_all('a')]
                sentences_without_links = [p.get_text(strip=True) for p in soup.find_all('p')]

                article_data_batch.append((url, occurrences, json.dumps(sentences_without_links), json.dumps(sentences_with_links)))
                console.log(f"Extracted data from {url}")

                if len(article_data_batch) >= batch_size:
                    await batch_insert_articles(pool, article_data_batch)
                    article_data_batch.clear()
                    console.log(f"Inserted batch of articles")

                async with pool.acquire() as conn:
                    last_inserted_id = await get_last_inserted_article_id(conn)
                console.log(f"Last inserted article ID: {last_inserted_id}")

                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.startswith('/'):
                        href = urljoin(url, href)
                    stripped_url = is_included(href, include_list)
                    if stripped_url:
                        link_data_batch.append((last_inserted_id, link.get_text(strip=True), stripped_url))
                console.log(f"Extracted links from {url}")

                if len(link_data_batch) >= batch_size:
                    await batch_insert_links(pool, link_data_batch)
                    link_data_batch.clear()
                    console.log(f"Inserted batch of links")

        except Exception as e:
            error_logger.error(f"An unexpected error occurred while processing {url}: {e}")
            error_logger.exception(e)
        finally:
            await crawled_queue.put(1)
            crawled_count = await crawled_queue.get()
            inserted_count = await inserted_queue.get()
            progress.update(task_id, advance=1, description=f"Crawled: {crawled_count} URLs, Inserted: {inserted_count} articles")
            console.log(f"Updated progress for {url}")
            
async def crawl_urls(start_url, search_string, pool, request_timeout, url_limit, 
                     include_list, concurrent_tasks, batch_size):
    crawled_urls = set()
    semaphore = asyncio.Semaphore(concurrent_tasks)
    article_data_batch = []
    link_data_batch = []
    crawled_queue = asyncio.Queue()
    inserted_queue = asyncio.Queue()

    bfs_queue = deque([(url_normalize(start_url), 0)])  # BFS Queue (URL, Depth)
    dfs_stack = []  # DFS Stack (URL, Depth)

    with Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%", style="cyan"),
        TimeRemainingColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Crawling", total=url_limit)
        tasks = []

        while (bfs_queue or dfs_stack) and len(crawled_urls) < url_limit:
            if bfs_queue and bfs_queue[0][1] <= 3:
                (url, depth) = bfs_queue.popleft()
            elif dfs_stack:
                (url, depth) = dfs_stack.pop()
            else:
                break

            if url not in crawled_urls:
                task_id = task
                task = asyncio.create_task(format_and_extract_data(
                    url, search_string, pool, request_timeout, crawled_urls,
                    semaphore, article_data_batch, link_data_batch, batch_size,
                    progress, task_id, crawled_queue, inserted_queue, include_list
                ))
                tasks.append(task)
                crawled_urls.add(url)
                console.log(f"Added {url} to crawled URLs")

                if depth < 3:
                    for link in await get_new_links(url, include_list):
                        normalized_link = url_normalize(link)
                        if normalized_link not in crawled_urls:
                            bfs_queue.append((normalized_link, depth + 1))
                            console.log(f"Added {normalized_link} to BFS queue")
                else:
                    for link in await get_new_links(url, include_list):
                        normalized_link = url_normalize(link)
                        if normalized_link not in crawled_urls:
                            dfs_stack.append((normalized_link, depth + 1))
                            console.log(f"Added {normalized_link} to DFS stack")

        # Await all tasks and ensure completion
        await asyncio.gather(*tasks)
        console.log("All tasks gathered and completed")

async def get_new_links(url, include_list):
    """Fetches a webpage and extracts new links from it."""
    new_links = []
    async with aiohttp.ClientSession() as session:
        try:
            content = await fetch(session, url)
            soup = BeautifulSoup(content, 'html.parser')
            for link in soup.find_all('a', href=True):
                href = link.get('href')
                if href.startswith('/'):
                    href = urljoin(url, href)
                stripped_url = is_included(href, include_list)
                if stripped_url and stripped_url not in new_links:
                    new_links.append(stripped_url)
        except aiohttp.ClientError as e:
            error_logger.error(f"HTTP error for URL {url}: {e}")
        except Exception as e:
            error_logger.error(f"Error fetching URL {url}: {e}")
    return new_links

async def main():
    console.log("Starting the crawler")
    pool = None
    try:
        # Load configuration
        default_config, db_config = get_config()
        console.log("Configuration loaded successfully")

        # Create DSN for PostgreSQL connection
        dsn = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}"
        console.log(f"DSN created: {dsn}")

        # Read settings from configuration
        start_url = default_config['start_url']
        url_limit = default_config['url_limit']
        include_list = default_config['include']
        concurrent_tasks = default_config['concurrent_tasks']
        batch_size = default_config['batch_size']

        console.log(f"Start URL from configuration: {start_url}")
        console.log(f"URL limit from configuration: {url_limit}")
        console.log(f"Inclusion list from configuration: {include_list}")
        console.log(f"Concurrent tasks: {concurrent_tasks}")
        console.log(f"Batch size: {batch_size}")

        # Establish connection pool
        pool = await asyncpg.create_pool(dsn)
        console.log("Database connection pool established")

        # Start the crawling process
        await crawl_urls(start_url, "prime day", pool, default_config['request_timeout'], 
                         url_limit, include_list, concurrent_tasks, batch_size)
        console.log("Crawling completed")

    except asyncpg.PostgresError as e:
        error_logger.error(f"Database error: {type(e).__name__} - {e}")
        error_logger.exception(e)
    except Exception as e:
        error_logger.error(f"Error in main: {type(e).__name__} - {e}")
        error_logger.exception(e)
    finally:
        if pool:
            await pool.close()
            console.log("Database connection pool closed")

if __name__ == "__main__":
    asyncio.run(main())

if __name__ == "__main__":
    asyncio.run(main())
