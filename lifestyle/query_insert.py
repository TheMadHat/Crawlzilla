import asyncpg
import asyncio
import logging
import argparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# PostgreSQL connection details
DB_HOST = 'localhost'
DB_NAME = 'lifestyle'
DB_USER = 'postgres'
DB_PASSWORD = 'JollyRoger123'
DB_PORT = '5432'

parser = argparse.ArgumentParser(description="Insert queries into PostgreSQL from a text file.")
parser.add_argument('text_file_path', type=str, help="The path to the text file containing queries and landing pages.")
args = parser.parse_args()

TEXT_FILE_PATH = args.text_file_path

async def insert_queries():
    logging.info("Starting query insertion process...")

    logging.info(f"Connecting to PostgreSQL database {DB_NAME} at {DB_HOST}:{DB_PORT}")
    conn = await asyncpg.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )

    # Read queries from the text file
    logging.info(f"Reading queries from {TEXT_FILE_PATH}")
    queries = []
    with open(TEXT_FILE_PATH, 'r') as file:
        for line in file:
            line = line.strip()
            if line:
                # Assuming the query and landing_page are separated by a comma
                query, landing_page = line.split(',', 1)
                queries.append((query.strip(), landing_page.strip()))

    logging.info(f"Number of Queries: {len(queries)}")

    # Initialize counters
    inserted_count = 0
    conflict_count = 0

    try:
        async with conn.transaction():
            logging.info("Inserting Queries into the database...")
            for query, landing_page in queries:
                # Check if the query already exists
                exists = await conn.fetchval('SELECT EXISTS(SELECT 1 FROM query WHERE query=$1)', query)
                if exists:
                    conflict_count += 1
                else:
                    await conn.execute('INSERT INTO query (query, landing_page) VALUES ($1, $2)', query, landing_page)
                    inserted_count += 1

            logging.info(f"Number of Queries inserted: {inserted_count}")
            logging.info(f"Number of conflicts (Queries already in database): {conflict_count}")
    except Exception as e:
        logging.error(f"An error occurred during query insertion: {e}")
    finally:
        # Close the database connection
        await conn.close()
        logging.info("Database connection closed.")

# Run the async function
if __name__ == "__main__":
    logging.info("Running the async query insertion script.")
    asyncio.run(insert_queries())
    logging.info("Script execution finished.")