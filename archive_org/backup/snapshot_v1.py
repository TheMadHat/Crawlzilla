import requests
import json
from datetime import datetime, timedelta
import re
import hashlib
import hmac
from urllib.parse import quote
import time

ACCESS_KEY = "Sx6LI12pEHc2HS0C"
SECRET_KEY = "co0wMscOEjV0Zfr5"

def get_auth_header(method, url, content_type=""):
    date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')
    parsed_url = requests.utils.urlparse(url)
    path = quote(parsed_url.path)
    
    string_to_sign = f"{method}\n\n{content_type}\n{date}\n{path}"
    signature = hmac.new(SECRET_KEY.encode('utf-8'), string_to_sign.encode('utf-8'), hashlib.sha1)
    auth_header = f'AWS {ACCESS_KEY}:{signature.hexdigest()}'
    
    return {
        'Authorization': auth_header,
        'Date': date
    }

def get_most_recent_relevant_redirect(url):
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=365)  # Start with the last year
    
    while start_date.year >= 1996:  # Wayback Machine's earliest year
        from_date = start_date.strftime("%Y%m%d")
        to_date = end_date.strftime("%Y%m%d")
        
        api_url = f"https://web.archive.org/cdx/search/cdx?url={url}&output=json&fl=original,timestamp,statuscode&from={from_date}&to={to_date}&reverse=1"
        headers = get_auth_header("GET", api_url)
        
        print("Making request to Wayback Machine API...")
        response = requests.get(api_url, headers=headers)
        
        if response.status_code != 200:
            print(f"Error: Unable to fetch data. Status code: {response.status_code}")
            return None
        
        data = json.loads(response.text)
        
        for entry in data[1:]:  # Skip the header row
            original, timestamp, status_code = entry
            if status_code.startswith('3'):
                print(f"Found potential redirect. Checking destination...")
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
        
        # If no relevant redirect found, move the search window back by a year
        end_date = start_date - timedelta(days=1)
        start_date = end_date - timedelta(days=365)
        print(f"No relevant redirects found in current time range. Moving back to {start_date.year}...")
        
        print("Waiting for 10 seconds before next request...")
        for i in range(10, 0, -1):
            print(f"Seconds remaining: {i}", end='\r')
            time.sleep(1)
        print("\n")
    
    return None

def get_destination_url(url, timestamp):
    playback_url = f"https://web.archive.org/web/{timestamp}/{url}"
    headers = get_auth_header("GET", playback_url)
    
    print("Checking destination URL...")
    response = requests.get(playback_url, allow_redirects=False, headers=headers)
    
    print("Waiting for 10 seconds before next request...")
    for i in range(10, 0, -1):
        print(f"Seconds remaining: {i}", end='\r')
        time.sleep(1)
    print("\n")
    
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