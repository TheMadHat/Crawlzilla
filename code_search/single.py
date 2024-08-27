#!/usr/bin/python3.12
# Crawls site and searches inside content for specified string and extracts links

import asyncio
import aiohttp
from bs4 import BeautifulSoup
from rich.console import Console
from rich.progress import Spinner
import logging
import configparser
import aiopg
from datetime import datetime
from urllib.parse import urlparse, urljoin
from aiohttp import ClientSession, ClientTimeout

# Initialize logging
logging.basicConfig(level=logging.INFO, handlers=[logging.FileHandler("monitor.log"), logging.StreamHandler()])
error_logger = logging.getLogger('error')
error_logger.addHandler(logging.FileHandler('error.log'))

# Initialize Rich console and spinner
console = Console()
spinner = Spinner("dots", "Crawling in progress...")

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
            'url_limit': int(config['DEFAULT']['url_limit'])
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

def get_db_config():
    _, db_config = get_config()
    return db_config

async def check_robots_txt(session: ClientSession, url: str) -> set:
    """
    Checks and parses the robots.txt file for disallowed paths.
    :param session: The aiohttp ClientSession.
    :param url: The base URL to check for robots.txt.
    :return: A set of disallowed paths.
    """
    parsed_url = urlparse(url)
    robots_url = urljoin(url, '/robots.txt')
    disallowed_paths = set()

    try:
        async with session.get(robots_url) as response:
            if response.status == 200:
                content = await response.text()
                for line in content.split('\n'):
                    if line.strip().lower().startswith('disallow:'):
                        path = line.split(':', 1)[1].strip()
                        disallowed_paths.add(urljoin(url, path))
    except aiohttp.ClientError as e:
        error_logger.error(f"Error fetching robots.txt: {e}")

    return disallowed_paths

async def batch_insert(data, table_name):
    """
    Asynchronously inserts a batch of data into the specified table.
    :param data: List of tuples containing data to insert.
    :param table_name: Name of the table to insert data into.
    """
    params = get_db_config()
    dsn = f"dbname={params['database']} user={params['user']} password={params['password']} host={params['host']}"

    async with aiopg.create_pool(dsn) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    if table_name == 'articles':
                        insert_query = f"""
                        INSERT INTO {table_name} (url, occurrences, sentences_without_links, sentences_with_links)
                        VALUES (%s, %s, %s, %s)
                        """
                    elif table_name == 'links':
                        insert_query = f"""
                        INSERT INTO {table_name} (article_id, anchor_text, link_destination)
                        VALUES (%s, %s, %s)
                        """
                    else:
                        raise ValueError("Unsupported table name")

                    await cursor.executemany(insert_query, data)
                    await conn.commit()
                except (Exception, aiopg.Error) as error:
                    error_logger.error(f"Error during batch insert: {error}")
                    await conn.rollback()

async def format_and_extract_data(url, search_string, dsn, disallowed_paths):
    """
    Fetches content from the URL, processes it to extract necessary data,
    and inserts the data into the database.
    :param url: URL to fetch content from.
    :param search_string: String to search for within the content.
    :param dsn: Data source name for the PostgreSQL database connection.
    :param disallowed_paths: Set of disallowed paths from robots.txt.
    """
    if any(url.startswith(disallowed_path) for disallowed_path in disallowed_paths):
        console.log(f"Skipping disallowed URL: {url}")
        return

    async with aiohttp.ClientSession(timeout=ClientTimeout(total=request_timeout)) as session:
        try:
            async with session.get(url, allow_redirects=max_redirects) as response:
                if response.status == 200:
                    content = await response.text()
                    soup = BeautifulSoup(content, 'html.parser')
                    content_div = soup.find('div', class_='caas-body')
                    if content_div:
                        paragraphs = content_div.find_all('p')
                        article_content = ' '.join([p.get_text(strip=True) for p in paragraphs]).lower()
                        occurrences = article_content.count(search_string)
                        
                        sentences_with_links = []
                        sentences_without_links = []
                        
                        for paragraph in paragraphs:
                            if search_string in paragraph.get_text().lower():
                                links = paragraph.find_all('a')
                                if links:
                                    for link in links:
                                        href = link.get('href')
                                        if 'shopping.yahoo.com' not in href:
                                            sentences_with_links.append({
                                                'sentence': paragraph.get_text(strip=True),
                                                'link': href,
                                                'anchor_text': link.get_text(strip=True)
                                            })
                                else:
                                    sentences_without_links.append(paragraph.get_text(strip=True))
                        
                        data_to_insert = (url, occurrences, len(sentences_without_links), len(sentences_with_links))
                        await insert_data(dsn, data_to_insert, sentences_with_links)
                else:
                    error_logger.error(f"Failed to retrieve {url}: HTTP status {response.status}")
        except aiohttp.ClientError as e:
            error_logger.error(f"Request error for {url}: {e}")

async def insert_data(dsn, article_data, link_data):
    """
    Inserts the extracted data into the database.
    :param dsn: Data source name for the PostgreSQL database connection.
    :param article_data: Tuple containing data to insert into the articles table.
    :param link_data: List of dictionaries containing data to insert into the links table.
    """
    async with aiopg.create_pool(dsn) as pool:
        async with pool.acquire() as conn:
            async with conn.cursor() as cursor:
                try:
                    # Insert article data
                    await cursor.execute(
                        "INSERT INTO articles (url, occurrences, sentences_without_links, sentences_with_links) VALUES (%s, %s, %s, %s) RETURNING id",
                        article_data
                    )
                    article_id = (await cursor.fetchone())[0]  # Fetch the returned article ID
                    
                    # Insert link data for each link in sentences_with_links
                    for link in link_data:
                        await cursor.execute(
                            "INSERT INTO links (article_id, anchor_text, link_destination) VALUES (%s, %s, %s)",
                            (article_id, link['anchor_text'], link['link'])
                        )
                    await conn.commit()
                except (Exception, aiopg.Error) as error:
                    error_logger.error(f"Error during data insertion: {error}")
                    await conn.rollback()

async def crawl_urls(urls, search_string, dsn, disallowed_paths):
    """
    Crawls multiple URLs concurrently.
    :param urls: List of URLs to crawl.
    :param search_string: String to search for within the content.
    :param dsn: Data source name for the PostgreSQL database connection.
    :param disallowed_paths: Set of disallowed paths from robots.txt.
    """
    tasks = []
    for url in urls:
        tasks.append(format_and_extract_data(url, search_string, dsn, disallowed_paths))
    
    await asyncio.gather(*tasks)

async def main():
    console.log("Starting the crawler")

    try:
        default_config, db_config = get_config()

        dsn = f"dbname={db_config['database']} user={db_config['user']} password={db_config['password']} host={db_config['host']}"
        
        async with aiohttp.ClientSession(timeout=ClientTimeout(total=default_config['request_timeout'])) as session:
            disallowed_paths = await check_robots_txt(session, default_config['start_url'])
            # Example URLs to crawl - replace with actual URLs
            urls = [default_config['start_url']]  # Add more URLs as needed
            with console.status("Crawling..."):
                await crawl_urls(urls, "search_string", dsn, disallowed_paths)
    except Exception as e:
        error_logger.error(f"Error in main: {e}")

if __name__ == "__main__":
    asyncio.run(main())