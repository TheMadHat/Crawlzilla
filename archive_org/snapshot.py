import requests
from random import randint
import json
from datetime import datetime, timedelta
import re

username = 'user-spzhkd6zn4-country-us'
password = '6aw2L4xoLm+GIl5eho'
proxy = f"http://{username}:{password}@us.smartproxy.com:10000"

SCRAPEOPS_API_KEY = '12906b07-2588-4779-b873-f3b1fded497c'

def get_headers_list():
  response = requests.get('http://headers.scrapeops.io/v1/browser-headers?api_key=' + SCRAPEOPS_API_KEY)
  json_response = response.json()
  return json_response.get('result', [])

def get_random_header(header_list):
  random_index = randint(0, len(header_list) - 1)
  return header_list[random_index]

header_list = get_headers_list()

def get_most_recent_relevant_redirect(url):
    while header_list != 0:
        api_url = f"https://web.archive.org/cdx/search/cdx?url={url}&output=json&fl=original,timestamp,statuscode"
        response = requests.get(api_url,headers=get_random_header(header_list), proxies = {
            'http': proxy, 
            'https': proxy
}
)
        
        if response.status_code != 200:
            print(f"Error: Unable to fetch data. Status code: {response.status_code}")
            return None
        
        data = json.loads(response.text)
        
        for entry in data[1:]:  # Skip the header row
            original, timestamp, status_code = entry
            if status_code.startswith('3'):
                destination = get_destination_url(original, timestamp)
                if destination:
                    stripped_destination = strip_wayback_url(destination)
                    if "/entry/" not in stripped_destination:
                        return {
                            'date': datetime.strptime(timestamp, "%Y%m%d%H%M%S").strftime("%Y-%m-%d %H:%M:%S"),
                            'from': original,
                            'to': stripped_destination,
                            'status_code': status_code
                        }
        
    return None

def get_destination_url(url, timestamp):
    playback_url = f"https://web.archive.org/web/{timestamp}/{url}"
    response = requests.get(playback_url, headers=get_random_header(header_list), proxies = {
            'http': proxy, 
            'https': proxy
}, allow_redirects=False)

    if 'Location' in response.headers:
        return response.headers['Location']
    return None

def strip_wayback_url(url):
    match = re.search(r'https?://web\.archive\.org/web/\d+/(https?://.*)', url)
    if match:
        return match.group(1)
    return url

def main():
    url = input("Enter the URL to check: ")
    redirect = get_most_recent_relevant_redirect(url)
    
    if redirect:
        print(f"Most recent relevant redirect:")
        print(f"Date: {redirect['date']}")
        print(f"From: {redirect['from']}")
        print(f"To: {redirect['to']}")
        print(f"Status Code: {redirect['status_code']}")
    else:
        print("No relevant redirects found.")

if __name__ == "__main__":
    main()
