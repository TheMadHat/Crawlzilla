import requests
from bs4 import BeautifulSoup

def get_title_and_status_code(url):
    try:
        response = requests.get(url, timeout=10)
        status_code = response.status_code
        if status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            title = soup.title.string if soup.title else "No Title Found"
        else:
            title = "N/A"
    except requests.exceptions.RequestException as e:
        status_code = "Error"
        title = str(e)
    
    return status_code, title

def main():
    with open('urls.txt', 'r') as file:
        urls = [line.strip() for line in file if line.strip()]
    
    for url in urls:
        status_code, title = get_title_and_status_code(url)
        print(f"URL: {url}\nStatus Code: {status_code}\nTitle: {title}\n")

if __name__ == "__main__":
    main()
