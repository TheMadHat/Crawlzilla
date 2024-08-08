import requests
from bs4 import BeautifulSoup

def scrape_kceventhub():
    url = 'https://kceventhub.com'
    response = requests.get(url)
    
    if response.status_code != 200:
        print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
        return
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    events = []

    # Assuming events are listed in a specific section or class, adjust the selectors as needed
    event_list = soup.find_all('div', class_='event')  # Adjust the class name based on the website's structure

    for event in event_list:
        title = event.find('h2', class_='event-title').text.strip()
        date = event.find('span', class_='event-date').text.strip()
        description = event.find('p', class_='event-description').text.strip()
        
        events.append({
            'title': title,
            'date': date,
            'description': description
        })
    
    return events

if __name__ == "__main__":
    events = scrape_kceventhub()
    if events:
        for event in events:
            print(f"Title: {event['title']}")
            print(f"Date: {event['date']}")
            print(f"Description: {event['description']}\n")
    else:
        print("No events found.")
