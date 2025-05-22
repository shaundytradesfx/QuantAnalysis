"""
Forex Factory scraper for economic calendar events.
"""
import requests
from bs4 import BeautifulSoup
import re
import datetime
import time
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
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        })
    
    def _fetch_with_retry(self, url: str) -> Optional[str]:
        """
        Fetch a URL with retry logic.
        
        Args:
            url (str): The URL to fetch.
            
        Returns:
            Optional[str]: The response text if successful, None otherwise.
        """
        current_retry = 0
        current_delay = self.retry_delay
        
        while current_retry < self.max_retries:
            try:
                logger.info(f"Fetching URL: {url}")
                response = self.session.get(url, timeout=10)
                
                if response.status_code == 200:
                    logger.info(f"Successfully fetched URL: {url}")
                    return response.text
                
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
    
    def scrape_calendar(self) -> List[Dict[str, Any]]:
        """
        Scrape the Forex Factory economic calendar.
        
        Returns:
            List[Dict[str, Any]]: A list of economic events.
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
        
        logger.info(f"Scraped {len(events)} high-impact events from Forex Factory.")
        return events 