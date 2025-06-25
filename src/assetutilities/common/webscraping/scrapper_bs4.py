import requests
from bs4 import BeautifulSoup
import re
import csv
import logging
import time
import random
from datetime import datetime
from typing import Dict, List, Optional, Union
from dataclasses import dataclass, asdict


# Configuration class for constants
class ScrapingConfig:
    BASE_URL = "https://www.loopnet.com/search/commercial-real-estate/usa/auctions/"
    REQUEST_TIMEOUT = 60  # Increased timeout
    REQUEST_DELAY = 2  # Increased delay
    MAX_RETRIES = 3
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    
    # Additional headers to appear more like a real browser
    HEADERS = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
        "DNT": "1",
        "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"'
    }


@dataclass
class ListingData:
    """Data structure for listing information"""
    title: Optional[str] = None
    subtitle: Optional[str] = None
    location: Optional[str] = None
    starting_bid: Optional[int] = None
    countdown: Optional[str] = None
    description: Optional[str] = None
    scraped_at: Optional[str] = None


class BS4Scrapper:
    def __init__(self):
        """Initialize scraper with session and logging"""
        # Setup logging
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        
        # Setup session for connection pooling and persistent headers
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": ScrapingConfig.USER_AGENT,
            **ScrapingConfig.HEADERS
        })
        
        # Configure session with additional settings
        self.session.verify = True
        self.session.max_redirects = 5
        
        # Set up adapter with retry strategy
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            method_whitelist=["HEAD", "GET", "OPTIONS"],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.request_delay = ScrapingConfig.REQUEST_DELAY

    def router(self, cfg: Dict) -> Dict:
        """Router function - keeping original conditions as requested"""
        if "source" in cfg['scrape_data'] and cfg['scrape_data']['source'] == 'loopnet':
            listings = self.scrape_auctions(ScrapingConfig.BASE_URL)
            success = self.export_to_csv(listings, "loopnet_auctions.csv")
            if success:
                self.logger.info("Scraping and export completed successfully")
            else:
                self.logger.error("Export failed")
        return cfg

    def scrape_auctions(self, url: str) -> List[Dict]:
        """Main scraping method with improved error handling"""
        self.logger.info(f"Starting to scrape auctions from {url}")
        
        try:
            # First, let's test if we can reach the URL
            self.logger.info("Testing connection to LoopNet...")
            html = self.fetch_html_with_retry(url)
            
            # Log some basic info about the response
            self.logger.info(f"Received HTML response with {len(html)} characters")
            
            soup = BeautifulSoup(html, "html.parser")
            
            # Debug: Check if we got the expected page structure
            title_tag = soup.find('title')
            if title_tag:
                self.logger.info(f"Page title: {title_tag.get_text()}")
            
            # Try multiple selectors in case the structure changed
            selectors_to_try = [
                "div#MainContent .placardDetails",
                ".placardDetails",
                ".property-card",
                ".listing-item",
                "[data-testid*='listing']",
                ".search-result-item"
            ]
            
            items = []
            for selector in selectors_to_try:
                items = soup.select(selector)
                if items:
                    self.logger.info(f"Found {len(items)} items using selector: {selector}")
                    break
                else:
                    self.logger.debug(f"No items found with selector: {selector}")
            
            if not items:
                self.logger.warning("No auction items found with any selector")
                # Debug: Save HTML snippet for analysis
                self.logger.debug(f"HTML snippet: {html[:2000]}...")
                return []
            
            self.logger.info(f"Found {len(items)} potential listings")
            
            listings = []
            for i, el in enumerate(items, 1):
                try:
                    data = self.parse_listing(el)
                    if data and self._validate_listing(data):
                        # Convert dataclass to dict for backward compatibility
                        listings.append(asdict(data) if isinstance(data, ListingData) else data)
                        self.logger.debug(f"Successfully parsed listing {i}")
                    else:
                        self.logger.warning(f"Skipping invalid listing {i}")
                except Exception as e:
                    self.logger.error(f"Failed to parse listing {i}: {e}")
                    continue
            
            self.logger.info(f"Successfully scraped {len(listings)} valid listings")
            return listings
            
        except Exception as e:
            self.logger.error(f"Critical error during scraping: {e}")
            return []

    def fetch_html_with_retry(self, url: str, max_retries: int = None) -> str:
        """Fetch HTML with retry logic and enhanced anti-detection measures"""
        if max_retries is None:
            max_retries = ScrapingConfig.MAX_RETRIES
            
        last_exception = None
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    # Progressive delay with randomization
                    delay = self.request_delay * (2 ** attempt) + random.uniform(0.5, 2.0)
                    self.logger.info(f"Waiting {delay:.1f} seconds before retry...")
                    time.sleep(delay)
                else:
                    # Random delay even on first attempt
                    initial_delay = self.request_delay + random.uniform(0.5, 1.5)
                    time.sleep(initial_delay)
                
                self.logger.info(f"Fetching {url} (attempt {attempt + 1}/{max_retries})")
                
                # Add some randomization to headers
                headers = self.session.headers.copy()
                headers['User-Agent'] = self._get_random_user_agent()
                
                response = self.session.get(
                    url, 
                    headers=headers,
                    timeout=ScrapingConfig.REQUEST_TIMEOUT,
                    allow_redirects=True
                )
                
                # Check for common anti-bot responses
                if self._is_blocked_response(response):
                    self.logger.warning(f"Potential bot detection on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        time.sleep(random.uniform(5, 10))  # Longer wait if blocked
                        continue
                
                response.raise_for_status()
                
                # Log response details for debugging
                self.logger.info(f"Response status: {response.status_code}, Size: {len(response.text)} chars")
                
                if len(response.text) < 1000:
                    self.logger.warning("Response seems too short, might be blocked")
                    self.logger.debug(f"Response preview: {response.text[:500]}")
                
                return response.text
                
            except requests.exceptions.Timeout as e:
                last_exception = e
                self.logger.warning(f"Timeout on attempt {attempt + 1}: {e}")
                
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                self.logger.warning(f"Connection error on attempt {attempt + 1}: {e}")
                
            except requests.exceptions.RequestException as e:
                last_exception = e
                self.logger.warning(f"Request failed on attempt {attempt + 1}: {e}")
                
            if attempt == max_retries - 1:
                self.logger.error(f"All {max_retries} attempts failed for {url}")
                raise last_exception
        
        # This shouldn't be reached, but just in case
        raise last_exception
    
    def _get_random_user_agent(self) -> str:
        """Return a random user agent to avoid detection"""
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
        ]
        return random.choice(user_agents)
    
    def _is_blocked_response(self, response) -> bool:
        """Check if response indicates bot detection"""
        # Check for common blocking indicators
        blocked_indicators = [
            'access denied',
            'blocked',
            'captcha',
            'robot',
            'bot detection',
            'security check',
            'cloudflare',
            'rate limit'
        ]
        
        response_text_lower = response.text.lower()
        for indicator in blocked_indicators:
            if indicator in response_text_lower:
                return True
                
        # Check for suspicious response codes or sizes
        if response.status_code in [403, 429, 503]:
            return True
            
        return False

    def parse_listing(self, el) -> Optional[Dict]:
        """Parse individual listing with improved data extraction"""
        try:
            # Extract title
            title = self._safe_extract_text(el.select_one("h4"))
            
            # Extract subtitle
            subtitle = self._safe_extract_text(el.select_one("h6"))
            
            # Extract location with improved ZIP code detection
            location = self._extract_location(el)
            
            # Extract price with better regex and cleaning
            starting_bid = self._extract_price(el)
            
            # Extract countdown
            countdown = self._extract_countdown(el)
            
            # Extract description
            description = self._extract_description(el)
            
            # Create listing data
            listing_data = {
                "title": title,
                "subtitle": subtitle,
                "location": location,
                "starting_bid": starting_bid,
                "countdown": countdown,
                "description": description,
                "scraped_at": datetime.now().isoformat()
            }
            
            return listing_data
            
        except Exception as e:
            self.logger.error(f"Error parsing listing element: {e}")
            return None

    def _safe_extract_text(self, element) -> Optional[str]:
        """Safely extract text from BeautifulSoup element"""
        if element and hasattr(element, 'get_text'):
            text = element.get_text(strip=True)
            return text if text else None
        return None

    def _extract_location(self, el) -> Optional[str]:
        """Extract location with improved ZIP code detection"""
        try:
            subtitle = el.select_one("h6")
            if not subtitle:
                return None
            
            # Look for ZIP code pattern in the subtitle itself first
            subtitle_text = subtitle.get_text(strip=True)
            zip_match = re.search(r'\b\d{5}(-\d{4})?\b', subtitle_text)
            if zip_match:
                return subtitle_text
            
            # Look in next siblings
            current = subtitle
            for _ in range(5):  # Limit search to avoid infinite loops
                current = current.find_next_sibling()
                if not current:
                    break
                    
                if hasattr(current, 'string') and current.string:
                    text = current.string.strip()
                    zip_match = re.search(r'\b\d{5}(-\d{4})?\b', text)
                    if zip_match:
                        return text
                elif hasattr(current, 'get_text'):
                    text = current.get_text(strip=True)
                    zip_match = re.search(r'\b\d{5}(-\d{4})?\b', text)
                    if zip_match:
                        return text
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error extracting location: {e}")
            return None

    def _extract_price(self, el) -> Optional[int]:
        """Extract starting bid price with improved regex"""
        try:
            # Look for "Starting bid" text
            price_element = el.find(string=re.compile(r"Starting bid", re.IGNORECASE))
            
            if price_element:
                # Extract numbers from the text, handling commas and currency symbols
                price_text = str(price_element)
                # Look for price patterns like $1,000,000 or 1000000
                price_match = re.search(r'[\$]?([0-9,]+)', price_text)
                if price_match:
                    # Remove commas and convert to int
                    price_str = price_match.group(1).replace(',', '')
                    if price_str.isdigit():
                        return int(price_str)
            
            # Alternative: look for price in nearby elements
            price_elements = el.find_all(string=re.compile(r'\$[0-9,]+'))
            for price_elem in price_elements:
                price_match = re.search(r'\$([0-9,]+)', str(price_elem))
                if price_match:
                    price_str = price_match.group(1).replace(',', '')
                    if price_str.isdigit():
                        return int(price_str)
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error extracting price: {e}")
            return None

    def _extract_countdown(self, el) -> Optional[str]:
        """Extract countdown information"""
        try:
            # Look for auction countdown selector (as in original code)
            countdown_elem = el.select_one("auction-countdown-selector")
            if countdown_elem:
                return countdown_elem.get_text(strip=True)
            
            # Alternative: look for time-related text
            time_elements = el.find_all(string=re.compile(r'(days?|hours?|minutes?|ends?)', re.IGNORECASE))
            if time_elements:
                return time_elements[0].strip()
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Error extracting countdown: {e}")
            return None

    def _extract_description(self, el) -> Optional[str]:
        """Extract and clean description text"""
        try:
            desc_items = []
            list_items = el.select("ul li")
            
            for li in list_items:
                text = li.get_text(strip=True)
                if text and len(text) > 1:  # Filter out empty or single-char items
                    desc_items.append(text)
            
            return " | ".join(desc_items) if desc_items else None
            
        except Exception as e:
            self.logger.debug(f"Error extracting description: {e}")
            return None

    def _validate_listing(self, listing_data: Dict) -> bool:
        """Validate that listing has minimum required data"""
        if not listing_data:
            return False
        
        # At minimum, we need a title
        required_fields = ['title']
        
        for field in required_fields:
            if not listing_data.get(field):
                return False
        
        return True

    def export_to_csv(self, listings: List[Dict], filename: str) -> bool:
        """Export listings to CSV with improved error handling"""
        if not listings:
            self.logger.warning("No listings to export")
            return False
        
        try:
            # Filter out None values from failed parsing
            valid_listings = [listing for listing in listings if listing is not None]
            
            if not valid_listings:
                self.logger.warning("No valid listings to export after filtering")
                return False
            
            # Get fieldnames from first valid listing
            fieldnames = list(valid_listings[0].keys())
            
            # Create CSV file
            with open(filename, "w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for listing in valid_listings:
                    try:
                        writer.writerow(listing)
                    except Exception as e:
                        self.logger.warning(f"Failed to write listing to CSV: {e}")
                        continue
            
            self.logger.info(f"Successfully exported {len(valid_listings)} listings to {filename}")
            return True
            
        except IOError as e:
            self.logger.error(f"Failed to create/write CSV file {filename}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during CSV export: {e}")
            return False

    def __del__(self):
        """Cleanup method to close session"""
        if hasattr(self, 'session'):
            try:
                self.session.close()
            except:
                pass
