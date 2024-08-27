import asyncio
import aiohttp
from bs4 import BeautifulSoup
import logging
import configparser
import asyncpg
from datetime import datetime
from urllib.parse import urlparse, urljoin, urlunparse
import traceback
from rich.console import Console
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from collections import deque

# Initialize logging
logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler("monitor.log")])
error_logger = logging.getLogger('error')
error_logger.setLevel(logging.ERROR)
error_logger.addHandler(logging.FileHandler('error.log'))

# Initialize Rich console and progress bar
console = Console()

def get_config():
    """
    Reads configuration details from the config.ini file.
    :return: A dictionary with the configuration details.
    """
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
    """
    Checks if the URL belongs to an included subdomain and does not contain query parameters.
    :param url: URL to check.
    :param include_list: List of subdomains to include.
    :return: True if the URL should be included, False otherwise.
    """
    parsed_url = urlparse(url)
    stripped_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, '', '', ''))
    if any(parsed_url.netloc.endswith(include) for include in include_list):
        return stripped_url
    return None

async def batch_insert_articles(conn, article_data_batch):
    """
    Asynchronously inserts a batch of article data into the 'articles' table.
    :param conn: Database connection.
    :param article_data_batch: List of article data tuples.
    """
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

async def batch_insert_links(conn, link_data_batch, last_inserted_id):
    """
    Asynchronously inserts a batch of link data into the 'links' table.
    :param conn: Database connection.
    :param link_data_batch: List of link data tuples.
    :param last_inserted_id: The ID of the last inserted article.
    """
    try:
        insert_query = """
        INSERT INTO links (article_id, anchor_text, link_destination)
        VALUES ($1, $2, $3)
        ON CONFLICT (article_id, anchor_text, link_destination) DO NOTHING
        """
        async with conn.transaction():
            await conn.executemany(insert_query, [(last_inserted_id, *link_data) for link_data in link_data_batch])
    except (Exception, asyncpg.PostgresError) as error:
        error_logger.error(f"Error during batch insert of links: {error}")

async def get_last_inserted_article_id(dsn):
    conn = await asyncpg.connect(dsn)
    try:
        query = "SELECT article_id FROM articles ORDER BY article_id DESC LIMIT 1"
        row = await conn.fetchrow(query)
        return row['article_id'] if row else None  # Return None if no rows found
    except (Exception, asyncpg.PostgresError) as error:
        error_logger.error(f"Error retrieving last inserted article_id: {error}")
    finally:
        await conn.close()

async def format_and_extract_data(url, search_string, dsn, request_timeout, crawled_urls, new_urls, include_list, semaphore, article_data_batch, link_data_batch, batch_size, progress, task_id, crawled_queue, inserted_queue):
    """
    Fetches content from the URL, processes it to extract necessary data,
    and inserts the data into the database. Discovers new URLs on the page.
    Handles redirects.
    :param url: URL to fetch content from.
    :param search_string: String to search for within the content.
    :param dsn: Data source name for the PostgreSQL database connection.
    :param request_timeout: Timeout for the request.
    :param crawled_urls: Set of already crawled URLs.
    :param new_urls: List to add newly discovered URLs.
    :param include_list: List of subdomains to include for crawling.
    :param semaphore: Semaphore to limit the number of concurrent tasks.
    :param article_data_batch: List to collect article data for batch insert.
    :param link_data_batch: List to collect link data for batch insert.
    :param batch_size: Size of the batch for batch insert.
    :param progress: Progress bar object.
    :param task_id: Progress task ID.
    :param crawled_queue: Queue for crawled URLs count.
    :param inserted_queue: Queue for inserted articles count.
    """
    async with semaphore:

        try:
            occurrences = 0
            sentences_without_links = []
            sentences_with_links = []
            retries = 3
            for attempt in range(retries):
                try:
                    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=request_timeout)) as session:
                        async with session.get(url, allow_redirects=True) as response:  # Allow redirects
                            if response.status == 200:
                                content = await response.text()
                                soup = BeautifulSoup(content, 'html.parser')
                                
                                # Discover new URLs
                                for link in soup.find_all('a', href=True):
                                    href = link.get('href')
                                    if href.startswith('/'):
                                        href = urljoin(url, href)
                                    stripped_url = is_included(href, include_list)
                                    if stripped_url and stripped_url not in crawled_urls and stripped_url not in new_urls:
                                        new_urls.append(stripped_url)
                                
                                # Find a more specific element to extract content from (adjust this as needed)
                                content_div = soup.find('div', class_='caas-body')  # Replace with appropriate class or ID
                                if content_div:
                                    paragraphs = content_div.find_all('p')
                                    article_content = ' '.join([p.get_text(strip=True) for p in paragraphs]).lower()
                                    
                                    occurrences = article_content.count(search_string) 
                                    sentences_with_links = []
                                    sentences_without_links = []
                                    
                                    for paragraph in paragraphs:
                                        paragraph_text = paragraph.get_text(strip=True).lower()
                                        if search_string in paragraph_text:
                                            links = paragraph.find_all('a')
                                            if links:
                                                for link in links:
                                                    href = link.get('href')
                                                    if 'shopping.yahoo.com' not in href:
                                                        sentences_with_links.append({
                                                            'sentence': paragraph_text,
                                                            'link': href,
                                                            'anchor_text': link.get_text(strip=True)
                                                        })
                                            else:
                                                sentences_without_links.append(paragraph_text)
                                    
                                # Insert article data and retrieve the article_id
                                article_data = (url, occurrences, len(sentences_without_links), len(sentences_with_links))
                                article_data_batch.append(article_data)

                                if len(article_data_batch) >= batch_size:
                                    conn = await asyncpg.connect(dsn)  # Await the connection
                                    try:
                                        await batch_insert_articles(conn, article_data_batch)
                                        await inserted_queue.put(len(article_data_batch))  # Update inserted count
                                        article_data_batch.clear()

                                        # Get the last inserted article_id (once after batch insert)
                                        last_inserted_id = await get_last_inserted_article_id(dsn)  

                                        # Associate links with the correct article_id
                                        for link in sentences_with_links:
                                            link_data_batch.append((link['anchor_text'], link['link']))

                                        if len(link_data_batch) >= batch_size: 
                                            await batch_insert_links(conn, link_data_batch, last_inserted_id)
                                            link_data_batch.clear() 
                                    finally:
                                        await conn.close()  # Close the connection after using it

                            else:
                                error_logger.error(f"Failed to retrieve {url}: HTTP status {response.status}")
                except (aiohttp.ClientConnectorError, aiohttp.ClientResponseError) as e:
                    error_logger.error(f"Request error for {url}: {e}")
                    await asyncio.sleep(1)
            else:
                error_logger.error(f"Failed to retrieve {url} after {retries} attempts.")
        except Exception as e:
            error_logger.error(f"An unexpected error occurred while processing {url}: {e}")
            error_logger.exception(e)
        finally:
            await crawled_queue.put(1)  # Update the crawled count
            crawled_count = await crawled_queue.get()
            inserted_count = await inserted_queue.get()
            progress.update(task_id, advance=1, description=f"Crawled: {crawled_count} URLs, Inserted: {inserted_count} articles")

async def crawl_urls(start_url, search_string, dsn, request_timeout, url_limit, include_list, concurrent_tasks, batch_size):
    """
    Crawls multiple URLs iteratively discovering new URLs.
    :param start_url: Starting URL to crawl.
    :param search_string: String to search for within the content.
    :param dsn: Data source name for the PostgreSQL database connection.
    :param request_timeout: Timeout for the request.
    :param url_limit: Limit for the number of URLs to crawl.
    :param include_list: List of subdomains to include for crawling.
    :param concurrent_tasks: Maximum number of concurrent tasks.
    :param batch_size: Size of the batch for batch insert.
    """
    crawled_urls = set()
    new_urls = [start_url]
    semaphore = asyncio.Semaphore(concurrent_tasks)
    article_data_batch = []
    link_data_batch = []

    crawled_queue = asyncio.Queue()
    inserted_queue = asyncio.Queue()

    with Progress(
        "[progress.description]{task.description}",
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%", style="cyan"),
        TimeRemainingColumn(),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("Crawling", total=url_limit)  # Create the progress task *outside* the loop

        tasks = []
        while new_urls and len(crawled_urls) < url_limit:
            while new_urls and len(tasks) < concurrent_tasks:
                url = new_urls.pop(0)
                if url not in crawled_urls:
                    task_id = task  # Assign the current task to task_id
                    tasks.append(asyncio.create_task(format_and_extract_data(url, search_string, dsn, request_timeout, 
                                                    crawled_urls, new_urls, include_list, 
                                                    semaphore, article_data_batch, link_data_batch, batch_size, 
                                                    progress, task_id, crawled_queue, inserted_queue)))
                    crawled_urls.add(url)

            if tasks:
                try:
                    await asyncio.gather(*tasks)
                    tasks = []  # Reset the tasks list after gathering them
                except Exception as e:
                    error_logger.error(f"Error during crawling: {type(e).__name__} - {e}")
                    error_logger.exception(e) 

        # Insert any remaining data in batches
        if article_data_batch:
            conn = await asyncpg.connect(dsn)  # Await the connection
            try:
                await batch_insert_articles(conn, article_data_batch)
                await inserted_queue.put(len(article_data_batch))  # Update inserted count
            finally:
                await conn.close()  # Close the connection
        if link_data_batch:
            conn = await asyncpg.connect(dsn)  # Await the connection
            try:
                last_inserted_id = await get_last_inserted_article_id(dsn)
                await batch_insert_links(conn, link_data_batch, last_inserted_id)
            finally:
                await conn.close()  # Close the connection

        crawled_count = await crawled_queue.get()
        inserted_count = await inserted_queue.get()
        progress.update(task, description=f"Crawled: {crawled_count} URLs, Inserted: {inserted_count} articles")

async def main():
    console.log("Starting the crawler")

    try:
        default_config, db_config = get_config()

        dsn = f"postgresql://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}"
        
        # Retrieve the start URL and inclusions from the configuration and log them for debugging
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

        await crawl_urls(start_url, "prime day", dsn, default_config['request_timeout'], url_limit, include_list, concurrent_tasks, batch_size)

    except Exception as e:
        error_logger.error(f"Error in main: {type(e).__name__} - {e}") 
        error_logger.exception(e)

if __name__ == "__main__":
    asyncio.run(main())
