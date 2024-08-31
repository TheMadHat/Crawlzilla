import requests
from bs4 import BeautifulSoup

def get_green_links(archive_url):
    response = requests.get(archive_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Find all green links (successfully archived)
    green_links = []
    for a_tag in soup.find_all('a', href=True):
        # Assuming 'green' links have a specific class or style
        if 'some-green-class' in a_tag.get('class', []):  # Adjust as necessary
            green_links.append(a_tag['href'])
    
    return green_links

def crawl_urls(urls):
    status_codes = {}
    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            status_codes[url] = response.status_code
        except requests.RequestException as e:
            status_codes[url] = f'Error: {e}'
    
    return status_codes

# Main script
archive_url = 'https://web.archive.org/web/20130815000000*/engadget.com/entry/1234000017043956/'
green_links = get_green_links(archive_url)
status_codes = crawl_urls(green_links)

for url, status in status_codes.items():
    print(f'URL: {url} - Status Code: {status}')