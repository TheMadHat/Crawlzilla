import requests
from time import sleep
from random import randint

# Load URLs from 'urls.txt'
with open('urls.txt', 'r') as file:
    urls = [line.strip() for line in file if line.strip()]

for url in urls:
    full_url = 'http://web.archive.org/cdx/search/cdx?url=' + url + '&filter=statuscode:301'
    response = requests.get(full_url)

    if response.status_code == 200:
        # Split the response text by space and extract the timestamp
        lines = response.text.splitlines()
        if lines:
            first_line = lines[0]
            parts = first_line.split()
            timestamp = parts[1]  # The timestamp is the second part after splitting by space

            # Construct the jump URL
            jump_url = f'https://web.archive.org/web/{timestamp}/{url}'

            # Make a HEAD request to get the headers only
            head_response = requests.head(jump_url, allow_redirects=False)

            # Extract the Location header if it exists
            if 'Location' in head_response.headers:
                location = head_response.headers['Location']

                # Find the position of 'www' and slice the string from there
                www_index = location.find('www')
                if www_index != -1:
                    original_url = 'https://' + location[www_index:]
                    with open('output.txt', 'a') as file:
                        print(f"Writing output to file for {full_url} | {original_url}")
                        output = f"{full_url} | {original_url}\n"
                        file.write(output)
                else:
                    print("Could not find 'www' in the Location URL.")
            else:
                print("No Location header found.")
        else:
            print("No data found in response.")
    else:
        print(f"Failed to fetch data, status code: {response.status_code}")
    
    sleep(randint(20, 40))
    print("Sleeping for 15-30 seconds...")