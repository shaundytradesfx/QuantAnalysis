"""
Tests for the Forex Factory scraper.
"""
import unittest
from unittest.mock import patch, MagicMock
import datetime
from bs4 import BeautifulSoup

from src.scraper.forex_factory import ForexFactoryScraper

class TestForexFactoryScraper(unittest.TestCase):
    """
    Tests for the ForexFactoryScraper class.
    """
    
    def setUp(self):
        """
        Set up test resources.
        """
        self.scraper = ForexFactoryScraper()
    
    def test_parse_date(self):
        """
        Test _parse_date method.
        """
        # Test valid date
        date_str = "Mon Jun 22"
        expected_date = datetime.datetime.strptime(f"{date_str} {datetime.datetime.now().year}", "%a %b %d %Y").date()
        parsed_date = self.scraper._parse_date(date_str)
        self.assertEqual(parsed_date, expected_date)
        
        # Test invalid date
        date_str = "Invalid date"
        parsed_date = self.scraper._parse_date(date_str)
        self.assertIsNone(parsed_date)
    
    def test_parse_time(self):
        """
        Test _parse_time method.
        """
        # Test valid time
        time_str = "8:30am"
        expected_time = datetime.time(8, 30)
        parsed_time = self.scraper._parse_time(time_str)
        self.assertEqual(parsed_time, expected_time)
        
        # Test empty time
        time_str = ""
        parsed_time = self.scraper._parse_time(time_str)
        self.assertIsNone(parsed_time)
        
        # Test invalid time
        time_str = "Invalid time"
        parsed_time = self.scraper._parse_time(time_str)
        self.assertIsNone(parsed_time)
    
    def test_parse_numeric_value(self):
        """
        Test _parse_numeric_value method.
        """
        # Test valid numeric value
        value_str = "2.5%"
        expected_value = 2.5
        parsed_value = self.scraper._parse_numeric_value(value_str)
        self.assertEqual(parsed_value, expected_value)
        
        # Test N/A value
        value_str = "N/A"
        parsed_value = self.scraper._parse_numeric_value(value_str)
        self.assertIsNone(parsed_value)
        
        # Test empty value
        value_str = ""
        parsed_value = self.scraper._parse_numeric_value(value_str)
        self.assertIsNone(parsed_value)
        
        # Test invalid value
        value_str = "Invalid"
        parsed_value = self.scraper._parse_numeric_value(value_str)
        self.assertIsNone(parsed_value)
    
    @patch('src.scraper.forex_factory.ForexFactoryScraper._fetch_with_retry')
    def test_scrape_calendar(self, mock_fetch):
        """
        Test scrape_calendar method.
        """
        # Load test HTML
        with open('tests/scraper/test_data/calendar_sample.html', 'r') as f:
            html_content = f.read()
        
        # Mock fetch response
        mock_fetch.return_value = html_content
        
        # Call method
        events = self.scraper.scrape_calendar()
        
        # Assertions
        mock_fetch.assert_called_once_with(self.scraper.CALENDAR_URL)
        self.assertTrue(len(events) > 0)
        
        # Check event structure
        event = events[0]
        self.assertIn('currency', event)
        self.assertIn('event_name', event)
        self.assertIn('scheduled_datetime', event)
        self.assertIn('impact_level', event)
        self.assertIn('previous_value', event)
        self.assertIn('forecast_value', event)

if __name__ == '__main__':
    unittest.main() 