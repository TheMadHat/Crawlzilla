import requests
from bs4 import BeautifulSoup
import json
from time import sleep
from random import randint

urls = [
    'engadget.com/entry/0141583269424672/&output=json',
    'engadget.com/entry/0253716515972351/&output=json'
]

status_codes = {}

for url in urls:
    full_url = 'http://web.archive.org/cdx/search/cdx?url=' + url + '&filter=statuscode:301'
    print(f"Fetching data from: {full_url}")
    response = requests.get(full_url)
    
    if response.status_code == 200:
        print(f"Successfully retrieved data for {url}")
        parse_url = response.json()
        
        # Process the returned JSON data
        for item in parse_url:
            timestamp = item[1]
            original_url = item[2]
            status_code = item[4]  # Assuming status code is at index 4
            status_codes[original_url] = status_code

            print(f"Processing URL: {original_url} with status code: {status_code}")

            if status_code == '301':
                final_url = f'https://web.archive.org/web/{timestamp}/{original_url}'
                print(f"Following redirect to: {final_url}")
                redirect_response = requests.get(final_url)
                sleep_duration = randint(5, 10)
                print(f"Sleeping for {sleep_duration} seconds before next operation")
                sleep(sleep_duration)

                if redirect_response.status_code == 200:
                    print(f"Successfully retrieved redirected page for {original_url}")
                    soup = BeautifulSoup(redirect_response.text, 'html.parser')
                    sleep_duration = randint(5, 10)
                    print(f"Sleeping for {sleep_duration} seconds before next operation")
                    sleep(sleep_duration)

                    # Check if "404 Not Found" exists in the page content
                    if "404 Not Found" not in redirect_response.text:
                        canonical_link = soup.find('link', rel='canonical')
                        sleep_duration = randint(5, 10)
                        print(f"Sleeping for {sleep_duration} seconds before next operation")
                        sleep(sleep_duration)

                        if canonical_link and canonical_link.get('href'):
                            canonical_url = canonical_link['href']
                            modified_url = canonical_url.replace('https://web.archive.org/web/', '').split('/', 2)[-1]
                            
                            modified_url = 'https://' + modified_url
                            output = f"{original_url} | {modified_url}\n"
                            print(f"Found canonical URL: {modified_url} for {original_url}")
                            sleep_duration = randint(5, 10)
                            print(f"Sleeping for {sleep_duration} seconds before next operation")
                            sleep(sleep_duration)

                            with open('output.txt', 'w') as file:
                                print(f"Writing output to file for {original_url}")
                                file.write(output)
                            
                            sleep_duration = randint(5, 10)
                            print(f"Sleeping for {sleep_duration} seconds before next operation")
                            sleep(sleep_duration)

                        else:
                            print(f"Canonical link not found for {final_url}")
                            with open('output.txt', 'w') as file:
                                file.write(f"Canonical link not found for {final_url}\n")
                            sleep_duration = randint(5, 10)
                            print(f"Sleeping for {sleep_duration} seconds before next operation")
                            sleep(sleep_duration)
                    
                    else:
                        print(f"404 Not Found detected in page content for {final_url}")
                        with open('output.txt', 'w') as file:
                                file.write(f"404 Not Found for {final_url}\n")
                    sleep_duration = randint(5, 10)
                    print(f"Sleeping for {sleep_duration} seconds before next operation")
                    sleep(sleep_duration)
    else:
        print(f"Failed to retrieve data for {url}: {response.status_code}")

    sleep_duration = randint(15, 30)
    print(f"Sleeping for {sleep_duration} seconds before processing next URL")
    sleep(sleep_duration)