import aiohttp
import asyncio

async def fetch(session, url):
    try:
        async with session.get(url) as response:
            return url, response.status
    except Exception as e:
        return url, str(e)

async def check_urls(file_path):
    async with aiohttp.ClientSession() as session:
        tasks = []
        with open(file_path, 'r') as file:
            urls = [line.strip() for line in file.readlines()]
            for url in urls:
                tasks.append(fetch(session, url))
        
        results = await asyncio.gather(*tasks)
        
        for url, status in results:
            print(f"{url}: {status}")

if __name__ == "__main__":
    file_path = "urls.txt"  # Replace with your file path
    asyncio.run(check_urls(file_path))
