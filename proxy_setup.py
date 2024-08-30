import requests
from random import randint

username = 'user-spzhkd6zn4-country-us'
password = '6aw2L4xoLm+GIl5eho'
proxy = f"http://{username}:{password}@us.smartproxy.com:10000"

SCRAPEOPS_API_KEY = '12906b07-2588-4779-b873-f3b1fded497c'

urls = [
    'https://ip.smartproxy.com/json',
    'https://ip.smartproxy.com/json'
]

def get_headers_list():
  response = requests.get('http://headers.scrapeops.io/v1/browser-headers?api_key=' + SCRAPEOPS_API_KEY)
  json_response = response.json()
  return json_response.get('result', [])

def get_random_header(header_list):
  random_index = randint(0, len(header_list) - 1)
  return header_list[random_index]

header_list = get_headers_list()

for url in urls:
    try:
        result = requests.get(url, headers=get_random_header(header_list), proxies = {
            'http': proxy, 
            'https': proxy
})
        print(result.text)

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        continue

