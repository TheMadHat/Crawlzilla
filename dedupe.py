from urllib.parse import urlparse, urlunparse
import os

input_file = 'parsed.txt'
output_file = 'temp.txt'

# Use a set to store unique URLs
unique_urls = set()

# Function to remove parameters and hash from the URL
def strip_url(url):
    parsed_url = urlparse(url)
    stripped_url = urlunparse((parsed_url.scheme, parsed_url.netloc, parsed_url.path, '', '', ''))
    return stripped_url

# Function to ensure URL has a trailing slash if it doesn't end in a file extension or already have one
def ensure_trailing_slash(url):
    if not url.endswith('/') and not os.path.splitext(url)[1]:
        url += '/'
    return url

# Read the input file and store unique URLs in the set
with open(input_file, 'r', encoding='utf-8') as file:
    for line in file:
        stripped_url = strip_url(line.strip())
        final_url = ensure_trailing_slash(stripped_url)
        unique_urls.add(final_url)

# Write the unique URLs back to a new output file
with open(output_file, 'w', encoding='utf-8') as file:
    for url in sorted(unique_urls):
        file.write(url + '\n')

print(f"Duplicates removed and URLs normalized. Unique URLs saved to {output_file}")
