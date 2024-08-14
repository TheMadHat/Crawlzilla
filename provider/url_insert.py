import asyncpg
import asyncio
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# PostgreSQL connection details
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_PORT = '5432'

# Path to the text file containing URLs
TEXT_FILE_PATH = 'urls.txt'

async def insert_urls():
    logging.info("Starting URL insertion process...")

    # Connect to the PostgreSQL database
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

    try:
        async with conn.transaction():
            logging.info("Inserting URLs into the database...")
            for url in urls:
                # Check if the URL already exists
                exists = await conn.fetchval('SELECT EXISTS(SELECT 1 FROM urls WHERE url=$1)', url)
                if exists:
                    conflict_count += 1
                else:
                    await conn.execute('INSERT INTO urls (url) VALUES ($1)', url)
                    inserted_count += 1

            logging.info(f"Number of URLs inserted: {inserted_count}")
            logging.info(f"Number of conflicts (URLs already in database): {conflict_count}")
    except Exception as e:
        logging.error(f"An error occurred during URL insertion: {e}")
    finally:
        # Close the database connection
        await conn.close()
        logging.info("Database connection closed.")

# Run the async function
if __name__ == "__main__":
    logging.info("Running the async URL insertion script.")
    asyncio.run(insert_urls())
    logging.info("Script execution finished.")