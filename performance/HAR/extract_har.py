import json
import csv

def extract_har_data(har_file_path):
    # Load the HAR file
    with open(har_file_path, 'r') as har_file:
        har_data = json.load(har_file)

    # Print top-level keys to understand the structure
    print("Top-level keys in HAR file:", har_data.keys())

    # Check if 'log' key exists in HAR data
    if 'log' not in har_data:
        print("Error: 'log' key not found in HAR file. Please check the file structure.")
        return None

    return har_data['log'].get('entries', [])

def get_header_value(headers, header_name):
    """Helper function to extract a specific header's value."""
    for header in headers:
        if header['name'].lower() == header_name.lower():
            return header['value']
    return 'N/A'

def extract_har_to_csv(har_file_path, csv_file_path):
    # Extract entries from the HAR data
    entries = extract_har_data(har_file_path)
    if entries is None or len(entries) == 0:
        print("Error: No entries found in the HAR file.")
        return

    # Define the CSV file headers
    headers = [
        'URL', 'HTTP Method', 'Status Code', 'Response Time (ms)', 'Content Size (bytes)',
        'Content Type', 'Start Time', 'End Time', 'DNS Lookup Time (ms)',
        'Connection Time (ms)', 'SSL/TLS Negotiation Time (ms)', 'Blocking Time (ms)',
        'Redirection Time (ms)', 'Cache Status', 'Transfer Size (bytes)', 'Initiator'
    ]

    # Open a CSV file for writing
    with open(csv_file_path, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(headers)  # Write the header row

        for entry in entries:
            request = entry['request']
            response = entry['response']
            timings = entry['timings']

            # Extract relevant data
            url = request['url']
            method = request['method']
            status = response['status']
            response_time = entry['time']  # Total time for the request
            content_size = response.get('content', {}).get('size', 0)
            content_type = response.get('content', {}).get('mimeType', 'N/A')
            start_time = entry['startedDateTime']
            end_time = timings.get('receive', 0) + timings.get('send', 0) + timings.get('wait', 0)
            dns_time = timings.get('dns', 0)
            connection_time = timings.get('connect', 0)
            ssl_time = timings.get('ssl', 0)
            blocking_time = timings.get('blocked', 0)
            redirect_time = timings.get('redirect', 0)
            cache_status = get_header_value(response.get('headers', []), 'x-cache')
            transfer_size = entry.get('_transferSize', content_size)
            initiator = entry.get('_initiator', {}).get('type', 'N/A')

            # Write the data row
            writer.writerow([
                url, method, status, response_time, content_size,
                content_type, start_time, end_time, dns_time,
                connection_time, ssl_time, blocking_time,
                redirect_time, cache_status, transfer_size, initiator
            ])

    print(f"Data has been successfully exported to {csv_file_path}")

# Example usage
har_file_path = 'new_test1_3g.har'  # Replace with your HAR file name
csv_file_path = 'output.csv'      # Replace with your desired CSV output path

extract_har_to_csv(har_file_path, csv_file_path)