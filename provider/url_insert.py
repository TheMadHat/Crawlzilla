import asyncpg
import asyncio
import os

# PostgreSQL connection details
DB_HOST = os.environ.get('DB_HOST')
DB_NAME = os.environ.get('DB_NAME')
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_PORT = '5432'

# Path to the text file containing URLs
TEXT_FILE_PATH = 'urls2.txt'

async def insert_urls():
    # Connect to the PostgreSQL database
    conn = await asyncpg.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=DB_PORT
    )

    # Read URLs from the text file
    with open(TEXT_FILE_PATH, 'r') as file:
        urls = [line.strip() for line in file if line.strip()]

    # Insert URLs into the PostgreSQL table
    async with conn.transaction():
        await conn.executemany(
            'INSERT INTO urls (url) VALUES ($1) ON CONFLICT DO NOTHING',
            [(url,) for url in urls]
        )

    # Close the database connection
    await conn.close()

# Run the async function
asyncio.run(insert_urls())