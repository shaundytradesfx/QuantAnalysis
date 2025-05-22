"""
Tests for the monitoring utilities.
"""
import unittest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime, timedelta

from src.utils.monitoring import (
    timing_decorator, 
    track_scraper_run, 
    get_last_successful_run, 
    check_scraper_health
)
from src.database.models import Config

class TestMonitoring(unittest.TestCase):
    """
    Tests for the monitoring utilities.
    """
    
    def test_timing_decorator(self):
        """
        Test timing_decorator function.
        """
        # Create a test function
        @timing_decorator
        def test_function():
            return "test"
        
        # Test that the function still returns the correct value
        result = test_function()
        self.assertEqual(result, "test")
    
    @patch('src.utils.monitoring.SessionLocal')
    def test_track_scraper_run_new_history(self, mock_session_local):
        """
        Test track_scraper_run function with new history.
        """
        # Setup mocks
        mock_db = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_db
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Call function
        track_scraper_run(events_count=10, success=True)
        
        # Assertions
        mock_db.query.assert_called_once_with(Config)
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        
        # Check that the correct Config object was added
        config = mock_db.add.call_args[0][0]
        self.assertEqual(config.key, "SCRAPER_RUN_HISTORY")
        
        # Parse the value and check it's a list with one item
        history = json.loads(config.value)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["events_count"], 10)
        self.assertEqual(history[0]["success"], True)
        self.assertIsNone(history[0]["error_message"])
    
    @patch('src.utils.monitoring.SessionLocal')
    def test_track_scraper_run_existing_history(self, mock_session_local):
        """
        Test track_scraper_run function with existing history.
        """
        # Setup mocks
        mock_db = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_db
        
        # Create a mock Config object with existing history
        existing_history = [
            {
                "timestamp": datetime.utcnow().isoformat(),
                "events_count": 5,
                "success": True,
                "error_message": None
            }
        ]
        mock_config = MagicMock(spec=Config)
        mock_config.key = "SCRAPER_RUN_HISTORY"
        mock_config.value = json.dumps(existing_history)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_config
        
        # Call function
        track_scraper_run(events_count=10, success=False, error_message="Test error")
        
        # Assertions
        mock_db.query.assert_called_once_with(Config)
        mock_db.add.assert_not_called()
        mock_db.commit.assert_called_once()
        
        # Parse the updated value and check the history
        history = json.loads(mock_config.value)
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["events_count"], 5)
        self.assertEqual(history[0]["success"], True)
        self.assertEqual(history[1]["events_count"], 10)
        self.assertEqual(history[1]["success"], False)
        self.assertEqual(history[1]["error_message"], "Test error")
    
    @patch('src.utils.monitoring.SessionLocal')
    def test_get_last_successful_run(self, mock_session_local):
        """
        Test get_last_successful_run function.
        """
        # Setup mocks
        mock_db = MagicMock()
        mock_session_local.return_value.__enter__.return_value = mock_db
        
        # Create a mock Config object with history
        successful_time = (datetime.utcnow() - timedelta(hours=2)).isoformat()
        history = [
            {
                "timestamp": (datetime.utcnow() - timedelta(hours=5)).isoformat(),
                "events_count": 5,
                "success": True,
                "error_message": None
            },
            {
                "timestamp": (datetime.utcnow() - timedelta(hours=3)).isoformat(),
                "events_count": 0,
                "success": False,
                "error_message": "Test error"
            },
            {
                "timestamp": successful_time,
                "events_count": 10,
                "success": True,
                "error_message": None
            },
            {
                "timestamp": datetime.utcnow().isoformat(),
                "events_count": 0,
                "success": False,
                "error_message": "Another error"
            }
        ]
        mock_config = MagicMock(spec=Config)
        mock_config.key = "SCRAPER_RUN_HISTORY"
        mock_config.value = json.dumps(history)
        mock_db.query.return_value.filter.return_value.first.return_value = mock_config
        
        # Call function
        result = get_last_successful_run()
        
        # Assertions
        self.assertEqual(result, successful_time)
    
    @patch('src.utils.monitoring.get_last_successful_run')
    def test_check_scraper_health_healthy(self, mock_get_last_successful_run):
        """
        Test check_scraper_health function with healthy scraper.
        """
        # Setup mock
        successful_time = (datetime.utcnow() - timedelta(hours=2)).isoformat()
        mock_get_last_successful_run.return_value = successful_time
        
        # Call function
        result = check_scraper_health()
        
        # Assertions
        self.assertTrue(result)
    
    @patch('src.utils.monitoring.get_last_successful_run')
    def test_check_scraper_health_unhealthy(self, mock_get_last_successful_run):
        """
        Test check_scraper_health function with unhealthy scraper.
        """
        # Setup mock
        successful_time = (datetime.utcnow() - timedelta(hours=25)).isoformat()
        mock_get_last_successful_run.return_value = successful_time
        
        # Call function
        result = check_scraper_health()
        
        # Assertions
        self.assertFalse(result)
    
    @patch('src.utils.monitoring.get_last_successful_run')
    def test_check_scraper_health_no_runs(self, mock_get_last_successful_run):
        """
        Test check_scraper_health function with no successful runs.
        """
        # Setup mock
        mock_get_last_successful_run.return_value = None
        
        # Call function
        result = check_scraper_health()
        
        # Assertions
        self.assertFalse(result)

if __name__ == '__main__':
    unittest.main() 