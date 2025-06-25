import requests
from bs4 import BeautifulSoup


class LoopNetScraper:
    def __init__(self):
        pass

    def scrape(self):
        # URL to scrape
        url = "https://www.loopnet.com/search/commercial-real-estate/usa/auctions/"
        # Send a GET request to the URL
        response = requests.get(url)

        # Check if the request was successful
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Find all the listings on the page
            listings = soup.find_all('div', class_='placardDetails')
            # Loop through each listing and extract the desired information
            for listing in listings:
                title = listing.find('a', class_='placardTitle').text.strip()
                address = listing.find('div', class_='placardAddress').text.strip()
                price = listing.find('div', class_='placardPrice').text.strip() if listing.find('div', class_='placardPrice') else 'N/A'
                
                print(f"Title: {title}")
                print(f"Address: {address}")
                print(f"Price: {price}")
                print("-" * 40)
        else:
            print(f"Failed to retrieve data. Status code: {response.status_code}")