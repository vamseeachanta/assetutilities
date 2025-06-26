import requests
from bs4 import BeautifulSoup

class LoopNetScraper:
    def __init__(self):
        pass

    def scrape(self):
        # URL to scrape
        url = "https://www.loopnet.com/search/commercial-real-estate/usa/auctions/"
        # Send a GET request to the URL
        response = requests.post(url)

        # Check if the request was successful
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            # find the container with the specific id
            container = soup.find(id="")
            