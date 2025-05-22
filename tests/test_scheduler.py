"""
Tests for the scheduler module.
"""
import unittest
from unittest.mock import patch, MagicMock

from src.scheduler import get_scraper_schedule_time, schedule_scraper

class TestScheduler(unittest.TestCase):
    """
    Tests for the scheduler module.
    """
    
    @patch('src.scheduler.os.getenv')
    def test_get_scraper_schedule_time_default(self, mock_getenv):
        """
        Test get_scraper_schedule_time function with default value.
        """
        # Setup mock
        mock_getenv.return_value = None
        
        # Call function
        result = get_scraper_schedule_time()
        
        # Assertions
        self.assertEqual(result, "02:00")
    
    @patch('src.scheduler.os.getenv')
    def test_get_scraper_schedule_time_custom(self, mock_getenv):
        """
        Test get_scraper_schedule_time function with custom value.
        """
        # Setup mock
        mock_getenv.return_value = "10:30"
        
        # Call function
        result = get_scraper_schedule_time()
        
        # Assertions
        self.assertEqual(result, "10:30")
    
    @patch('src.scheduler.BackgroundScheduler')
    @patch('src.scheduler.get_scraper_schedule_time')
    def test_schedule_scraper(self, mock_get_time, mock_scheduler_class):
        """
        Test schedule_scraper function.
        """
        # Setup mocks
        mock_get_time.return_value = "04:30"
        mock_scheduler = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler
        
        # Call function
        result = schedule_scraper()
        
        # Assertions
        self.assertEqual(result, mock_scheduler)
        mock_scheduler.add_job.assert_called_once()
        
        # Check that the job was added with the correct parameters
        args = mock_scheduler.add_job.call_args[0]
        kwargs = mock_scheduler.add_job.call_args[1]
        
        from src.run_scraper import run_scraper
        self.assertEqual(args[0], run_scraper)
        self.assertEqual(kwargs["id"], "forex_factory_scraper")
        self.assertEqual(kwargs["name"], "Forex Factory Scraper")
        self.assertEqual(kwargs["replace_existing"], True)
        
        # Check the trigger
        trigger = kwargs["trigger"]
        self.assertEqual(trigger.fields[2], 4)  # hour
        self.assertEqual(trigger.fields[1], 30)  # minute

if __name__ == '__main__':
    unittest.main() 