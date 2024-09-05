#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# This script inserts URLs into a PostgreSQL database from a text file.
# It reads URLs from a text file, determines their priority, and inserts them into the 'discovery' table.
# If a URL has query parameters, it inserts the URL into the 'parameters' table as well.
# The script uses the following priority rules:
# - If the URL ends with ".html", the priority is the minimum of 2 and the depth of the URL.
# - If the URL contains any of the patterns "/live/", "/quote/", "/horoscope/", "/weather/", "/games/", the priority is 1.
# - If the URL contains any of the keywords "prime-day", "election", "black-friday", "taylor-swift", "trump", "stock-market", "dow-jones", "super-bowl", "congress", "senate", "vance", "walz", "harris", "amazon-prime", "cyber-monday", the priority is 1.
# - Otherwise, the priority is the minimum of 4 and the depth of the URL.
# The script processes URLs with query parameters by removing the query and fragment, counting the number of query string keys, and determining if there are more than 3 query string keys.
# The script inserts the URL into the 'discovery' table and checks for conflicts (URLs already in the database).
# The script also inserts the URL into the 'parameters' table if it has query parameters.
# The script logs the number of URLs read, inserted, conflicts, and any errors that occur during the insertion process.

import asyncpg
import asyncio
import os
import logging
import argparse
from urllib.parse import urlparse, parse_qs

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# PostgreSQL connection details
DB_HOST = 'localhost'
DB_NAME = 'index'
DB_USER = 'postgres'
DB_PASSWORD = 'JollyRoger123'
DB_PORT = '5432'
BATCH_SIZE = 2000  # Batch size for inserting URLs

parser = argparse.ArgumentParser(description="Insert URLs into PostgreSQL from a text file.")
parser.add_argument('text_file_path', type=str, help="The path to the text file containing URLs.")
args = parser.parse_args()

TEXT_FILE_PATH = args.text_file_path

# Priority rules
def determine_priority(url):
    path = urlparse(url).path
    depth = path.strip('/').count('/') + 1

    if url.endswith(".html"):
        return min(2, depth)
    elif any(pattern in url for pattern in ["/live/", "/quote/", "/horoscope/", "/weather/", "/games/"]):
        return 1
    elif any(keyword in url for keyword in ["prime-day", "election", "black-friday", "taylor-swift", "trump", "stock-market", "dow-jones", "super-bowl", "congress", "senate", "vance", "walz", "harris", "amazon-prime", "cyber-monday"]):
        return 1
    else:
        return min(4, depth)

# Handle URLs with parameters
def process_url_with_parameters(url):
    parsed_url = urlparse(url)
    stripped_url = parsed_url._replace(query="", fragment="").geturl()  # Remove query and fragment
    query_string = parsed_url.query
    query_dict = parse_qs(query_string)
    q_string_count = len(query_dict)  # Count number of query string keys
    more_than_3 = q_string_count > 3

    return stripped_url, query_string, q_string_count, more_than_3

async def insert_urls():
    logging.info("Starting URL insertion process...")

    logging.info(f"Connecting to PostgreSQL database {DB_NAME} at {DB_HOST}:{DB_PORT}")
    conn = await asyncpg.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )

    # Read URLs from the text file
    logging.info(f"Reading URLs from {TEXT_FILE_PATH}")
    with open(TEXT_FILE_PATH, 'r') as file:
        urls = [line.strip() for line in file if line.strip()]

    logging.info(f"Number of URLs read: {len(urls)}")

    # Initialize counters
    inserted_count = 0
    conflict_count = 0

    # Batch processing
    for i in range(0, len(urls), BATCH_SIZE):
        batch = urls[i:i + BATCH_SIZE]
        logging.info(f"Inserting batch {i // BATCH_SIZE + 1} with {len(batch)} URLs...")

        try:
            async with conn.transaction():
                for url in batch:
                    priority = determine_priority(url)
                    parsed_url = urlparse(url)

                    # Check if there are query parameters
                    if parsed_url.query or parsed_url.fragment:
                        stripped_url, query_string, q_string_count, more_than_3 = process_url_with_parameters(url)

                        # Insert into 'parameters' table
                        try:
                            await conn.execute(
                                'INSERT INTO parameters (url, p_string, q_strings, more_3) VALUES ($1, $2, $3, $4)',
                                stripped_url, query_string, q_string_count, more_than_3
                            )
                            logging.info(f"Inserted parameters for {url}")
                        except asyncpg.UniqueViolationError:
                            logging.warning(f"Parameters for {url} already exist in the parameters table.")
                    else:
                        stripped_url = url

                    # Insert into 'discovery' table
                    exists = await conn.fetchval('SELECT EXISTS(SELECT 1 FROM discovery WHERE url=$1)', stripped_url)
                    if exists:
                        conflict_count += 1
                    else:
                        await conn.execute(
                            'INSERT INTO discovery (url, priority) VALUES ($1, $2)',
                            stripped_url, priority
                        )
                        inserted_count += 1

        except Exception as e:
            logging.error(f"An error occurred during URL insertion: {e}")

    logging.info(f"Total number of URLs inserted: {inserted_count}")
    logging.info(f"Total number of conflicts (URLs already in database): {conflict_count}")

    # Close the database connection
    await conn.close()
    logging.info("Database connection closed.")

# Run the async function
if __name__ == "__main__":
    logging.info("Running the async URL insertion script.")
    asyncio.run(insert_urls())
    logging.info("Script execution finished.")
