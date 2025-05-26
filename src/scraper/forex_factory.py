"""
Forex Factory scraper for economic calendar events.
"""
import requests
from bs4 import BeautifulSoup
import re
import datetime
import time
import random
import json
from dateutil import parser as date_parser
from typing import List, Dict, Optional, Tuple, Any
from urllib.parse import urljoin

from src.utils.logging import get_logger

logger = get_logger(__name__)

class ForexFactoryScraper:
    """
    Scraper for Forex Factory economic calendar.
    """
    BASE_URL = "https://www.forexfactory.com"
    CALENDAR_URL = f"{BASE_URL}/calendar.php"
    JSON_API_URL = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
    
    def __init__(self, max_retries: int = 3, retry_delay: int = 2):
        """
        Initialize the scraper.
        
        Args:
            max_retries (int): Maximum number of retries for HTTP requests.
            retry_delay (int): Initial delay between retries in seconds (will be exponentially increased).
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.session = requests.Session()
        
        # Enhanced headers to appear more like a real browser
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0"
        })
    
    def _fetch_with_retry(self, url: str) -> Optional[str]:
        """
        Fetch a URL with retry logic and anti-bot detection avoidance.
        
        Args:
            url (str): The URL to fetch.
            
        Returns:
            Optional[str]: The response text if successful, None otherwise.
        """
        current_retry = 0
        current_delay = self.retry_delay
        
        while current_retry < self.max_retries:
            try:
                # Add random delay to appear more human-like
                if current_retry > 0:
                    delay = random.uniform(1.0, 3.0)
                    logger.info(f"Adding random delay of {delay:.2f} seconds")
                    time.sleep(delay)
                
                logger.info(f"Fetching URL: {url}")
                
                # First, visit the main page to establish session
                if current_retry == 0:
                    logger.info("Establishing session by visiting main page...")
                    main_response = self.session.get(self.BASE_URL, timeout=15, allow_redirects=True)
                    if main_response.status_code == 200:
                        logger.info("Successfully established session")
                        # Add a small delay after visiting main page
                        time.sleep(random.uniform(0.5, 1.5))
                    else:
                        logger.warning(f"Failed to establish session, status: {main_response.status_code}")
                
                # Now fetch the calendar page
                response = self.session.get(url, timeout=15, allow_redirects=True)
                
                if response.status_code == 200:
                    logger.info(f"Successfully fetched URL: {url}")
                    return response.text
                elif response.status_code == 403:
                    logger.warning(f"Access forbidden (403) for URL: {url}. Trying different approach...")
                    # Try with different headers
                    self._rotate_user_agent()
                elif response.status_code == 429:
                    logger.warning(f"Rate limited (429) for URL: {url}. Adding longer delay...")
                    time.sleep(random.uniform(5.0, 10.0))
                else:
                    logger.warning(f"Failed to fetch URL: {url}, status code: {response.status_code}")
                
            except (requests.RequestException, ConnectionError) as e:
                logger.error(f"Error fetching URL: {url}, error: {str(e)}")
            
            current_retry += 1
            if current_retry < self.max_retries:
                logger.info(f"Retrying in {current_delay} seconds (attempt {current_retry+1}/{self.max_retries})")
                time.sleep(current_delay)
                current_delay *= 2  # Exponential backoff
        
        logger.error(f"Failed to fetch URL after {self.max_retries} retries: {url}")
        return None
    
    def _rotate_user_agent(self):
        """
        Rotate to a different user agent to avoid detection.
        """
        user_agents = [
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ]
        
        new_ua = random.choice(user_agents)
        self.session.headers.update({"User-Agent": new_ua})
        logger.info(f"Rotated to new user agent: {new_ua[:50]}...")
    
    def _parse_date(self, date_str: str) -> Optional[datetime.date]:
        """
        Parse a date string from Forex Factory.
        
        Args:
            date_str (str): The date string to parse.
            
        Returns:
            Optional[datetime.date]: The parsed date if successful, None otherwise.
        """
        try:
            # Format is usually "Mon Jun 22" or similar
            now = datetime.datetime.now()
            # This is a simplified parsing, might need adjustment based on actual format
            parsed_date = datetime.datetime.strptime(f"{date_str} {now.year}", "%a %b %d %Y").date()
            
            # If the parsed date is more than 6 months in the future, it's probably last year
            if (parsed_date - now.date()).days > 180:
                parsed_date = datetime.datetime.strptime(f"{date_str} {now.year-1}", "%a %b %d %Y").date()
                
            return parsed_date
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing date: {date_str}, error: {str(e)}")
            return None
    
    def _parse_time(self, time_str: str) -> Optional[datetime.time]:
        """
        Parse a time string from Forex Factory.
        
        Args:
            time_str (str): The time string to parse.
            
        Returns:
            Optional[datetime.time]: The parsed time if successful, None otherwise.
        """
        if not time_str or time_str.strip() == "":
            return None
            
        try:
            # Format is usually "8:30am" or similar
            return datetime.datetime.strptime(time_str.strip(), "%I:%M%p").time()
        except (ValueError, TypeError) as e:
            logger.error(f"Error parsing time: {time_str}, error: {str(e)}")
            return None
    
    def _parse_numeric_value(self, value_str: str) -> Optional[float]:
        """
        Parse a numeric value from Forex Factory.
        
        Args:
            value_str (str): The value string to parse.
            
        Returns:
            Optional[float]: The parsed value if successful, None otherwise.
        """
        if not value_str or value_str.strip() in ["", "N/A", "-"]:
            return None
            
        try:
            # Remove % and other non-numeric characters
            clean_val = re.sub(r'[^\d.-]', '', value_str)
            return float(clean_val)
        except (ValueError, TypeError) as e:
            logger.warning(f"Error parsing numeric value: {value_str}, error: {str(e)}")
            return None
    
    def _fetch_json_calendar(self) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch calendar data from the JSON API endpoint.
        
        Returns:
            Optional[List[Dict[str, Any]]]: List of events from JSON API, None if failed.
        """
        max_retries = 3
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Fetching calendar data from JSON API: {self.JSON_API_URL} (attempt {attempt + 1}/{max_retries})")
                
                # Use a simple session without compression headers for JSON API
                simple_headers = {
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "en-US,en;q=0.9"
                }
                
                response = requests.get(self.JSON_API_URL, headers=simple_headers, timeout=15)
                
                if response.status_code == 200:
                    logger.info("Successfully fetched JSON calendar data")
                    logger.debug(f"Response content type: {response.headers.get('content-type')}")
                    logger.debug(f"Response length: {len(response.text)}")
                    return response.json()
                elif response.status_code == 429:
                    logger.warning(f"Rate limited (429), waiting {retry_delay} seconds before retry...")
                    if attempt < max_retries - 1:
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        continue
                else:
                    logger.warning(f"Failed to fetch JSON calendar, status code: {response.status_code}")
                    return None
                    
            except (requests.RequestException, json.JSONDecodeError) as e:
                logger.error(f"Error fetching JSON calendar: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2
                    continue
                return None
        
        logger.error(f"Failed to fetch JSON calendar after {max_retries} attempts")
        return None
    
    def _parse_json_events(self, json_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Parse events from JSON API data.
        
        Args:
            json_data (List[Dict[str, Any]]): Raw JSON data from API.
            
        Returns:
            List[Dict[str, Any]]: Parsed events in our standard format.
        """
        events = []
        
        for item in json_data:
            try:
                # Skip non-high impact events
                impact_level = item.get('impact', '').strip()
                if impact_level != 'High':
                    continue
                
                # Extract basic fields
                title = item.get('title', '').strip()
                country = item.get('country', '').strip()
                date_str = item.get('date', '').strip()
                forecast_str = item.get('forecast', '').strip()
                previous_str = item.get('previous', '').strip()
                
                # Skip if missing essential data
                if not all([title, country, date_str]):
                    continue
                
                # Parse datetime
                try:
                    scheduled_datetime = date_parser.parse(date_str)
                    # Convert to UTC if it has timezone info
                    if scheduled_datetime.tzinfo is not None:
                        scheduled_datetime = scheduled_datetime.utctimetuple()
                        scheduled_datetime = datetime.datetime(*scheduled_datetime[:6])
                except (ValueError, TypeError) as e:
                    logger.warning(f"Failed to parse date '{date_str}': {e}")
                    continue
                
                # Parse numeric values
                previous_value = self._parse_numeric_value(previous_str)
                forecast_value = self._parse_numeric_value(forecast_str)
                
                # Create event
                event = {
                    "currency": country,
                    "event_name": title,
                    "scheduled_datetime": scheduled_datetime,
                    "impact_level": impact_level,
                    "previous_value": previous_value,
                    "forecast_value": forecast_value
                }
                
                events.append(event)
                logger.debug(f"Parsed event: {country} - {title} at {scheduled_datetime}")
                
            except Exception as e:
                logger.warning(f"Error parsing event {item}: {e}")
                continue
        
        logger.info(f"Parsed {len(events)} high-impact events from JSON API")
        return events
    
    def scrape_calendar(self) -> List[Dict[str, Any]]:
        """
        Scrape the Forex Factory economic calendar.
        Prioritizes JSON API as requested, with HTML fallback only if JSON completely fails.
        
        Returns:
            List[Dict[str, Any]]: A list of economic events.
        """
        # Try JSON API first (with retries and rate limiting handling)
        json_data = self._fetch_json_calendar()
        if json_data:
            events = self._parse_json_events(json_data)
            logger.info(f"Successfully scraped {len(events)} events from JSON API")
            return events
        else:
            logger.warning("JSON API failed completely after retries, trying HTML fallback")
        
        # Fallback to HTML scraping only if JSON API completely fails
        return self._scrape_html_calendar()
    
    def _scrape_html_calendar(self) -> List[Dict[str, Any]]:
        """
        Fallback HTML scraping method.
        
        Returns:
            List[Dict[str, Any]]: A list of economic events from HTML parsing.
        """
        html_content = self._fetch_with_retry(self.CALENDAR_URL)
        if not html_content:
            logger.error("Failed to fetch calendar HTML.")
            return []
        
        soup = BeautifulSoup(html_content, 'lxml')
        
        # Find the calendar table
        calendar_table = soup.find('table', class_='calendar__table')
        if not calendar_table:
            logger.error("Could not find calendar table in HTML.")
            return []
        
        events = []
        current_date = None
        
        # Process each row in the table
        for row in calendar_table.find_all('tr'):
            # Check if this is a date row
            date_cell = row.find('td', class_='calendar__date')
            if date_cell and date_cell.text.strip():
                current_date = self._parse_date(date_cell.text.strip())
                continue
            
            # Check if this is an event row and get impact level
            impact_cell = row.find('td', class_='calendar__impact')
            if not impact_cell:
                continue
                
            impact_span = impact_cell.find('span')
            if not impact_span:
                continue
                
            # Extract impact level from class (e.g., "high" from "icon--ff-impact-3 icon--ff-impact-3-high")
            impact_classes = impact_span.get('class', [])
            impact_level = "Low"  # Default
            
            for cls in impact_classes:
                if "high" in cls:
                    impact_level = "High"
                    break
                elif "medium" in cls:
                    impact_level = "Medium"
                    break
            
            # Only process high-impact events
            if impact_level != "High":
                continue
            
            # Get other cells
            time_cell = row.find('td', class_='calendar__time')
            currency_cell = row.find('td', class_='calendar__currency')
            event_cell = row.find('td', class_='calendar__event')
            previous_cell = row.find('td', class_='calendar__previous')
            forecast_cell = row.find('td', class_='calendar__forecast')
            
            # Skip if any required cell is missing
            if not all([time_cell, currency_cell, event_cell]):
                continue
            
            # Extract data
            time_str = time_cell.text.strip() if time_cell else ""
            currency = currency_cell.text.strip() if currency_cell else ""
            event_name = event_cell.text.strip() if event_cell else ""
            previous_value = self._parse_numeric_value(previous_cell.text.strip()) if previous_cell else None
            forecast_value = self._parse_numeric_value(forecast_cell.text.strip()) if forecast_cell else None
            
            # Create datetime object
            event_time = self._parse_time(time_str)
            
            if current_date and event_time:
                scheduled_datetime = datetime.datetime.combine(current_date, event_time)
            else:
                # If we can't parse the time, use the date with midnight time
                scheduled_datetime = datetime.datetime.combine(current_date, datetime.time(0, 0)) if current_date else None
            
            # Add to events list
            if currency and event_name and scheduled_datetime:
                events.append({
                    "currency": currency,
                    "event_name": event_name,
                    "scheduled_datetime": scheduled_datetime,
                    "impact_level": impact_level,
                    "previous_value": previous_value,
                    "forecast_value": forecast_value
                })
        
        logger.info(f"Scraped {len(events)} high-impact events from HTML.")
        return events 