"""
Tests for the health check module.
"""
import unittest
from unittest.mock import patch, MagicMock
import os

from src.health_check import send_health_alert, check_health, run_health_check

class TestHealthCheck(unittest.TestCase):
    """
    Tests for the health check module.
    """
    
    @patch('src.health_check.requests.post')
    @patch('src.health_check.os.getenv')
    def test_send_health_alert_success(self, mock_getenv, mock_post):
        """
        Test send_health_alert function with successful response.
        """
        # Setup mocks
        mock_getenv.return_value = "https://discord.webhook.url"
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Call function
        result = send_health_alert("Test alert")
        
        # Assertions
        self.assertTrue(result)
        mock_post.assert_called_once()
        
        # Check that the payload contains the alert message
        payload = mock_post.call_args[1]["json"]
        self.assertIn("Test alert", payload["content"])
    
    @patch('src.health_check.requests.post')
    @patch('src.health_check.os.getenv')
    def test_send_health_alert_failure(self, mock_getenv, mock_post):
        """
        Test send_health_alert function with failed response.
        """
        # Setup mocks
        mock_getenv.return_value = "https://discord.webhook.url"
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response
        
        # Call function
        result = send_health_alert("Test alert")
        
        # Assertions
        self.assertFalse(result)
    
    @patch('src.health_check.os.getenv')
    def test_send_health_alert_no_webhook(self, mock_getenv):
        """
        Test send_health_alert function with no webhook URL.
        """
        # Setup mock
        mock_getenv.return_value = None
        
        # Call function
        result = send_health_alert("Test alert")
        
        # Assertions
        self.assertFalse(result)
    
    @patch('src.health_check.check_scraper_health')
    @patch('src.health_check.send_health_alert')
    def test_check_health_healthy(self, mock_send_alert, mock_check_scraper):
        """
        Test check_health function with healthy scraper.
        """
        # Setup mock
        mock_check_scraper.return_value = True
        
        # Call function
        result = check_health()
        
        # Assertions
        self.assertTrue(result)
        mock_send_alert.assert_not_called()
    
    @patch('src.health_check.check_scraper_health')
    @patch('src.health_check.send_health_alert')
    @patch('src.health_check.get_last_successful_run')
    def test_check_health_unhealthy_with_last_run(self, mock_get_last_run, mock_send_alert, mock_check_scraper):
        """
        Test check_health function with unhealthy scraper and last run.
        """
        # Setup mocks
        mock_check_scraper.return_value = False
        import datetime
        last_run = (datetime.datetime.utcnow() - datetime.timedelta(hours=5)).isoformat()
        mock_get_last_run.return_value = last_run
        
        # Call function
        result = check_health()
        
        # Assertions
        self.assertFalse(result)
        mock_send_alert.assert_called_once()
    
    @patch('src.health_check.check_scraper_health')
    @patch('src.health_check.send_health_alert')
    @patch('src.health_check.get_last_successful_run')
    def test_check_health_unhealthy_no_last_run(self, mock_get_last_run, mock_send_alert, mock_check_scraper):
        """
        Test check_health function with unhealthy scraper and no last run.
        """
        # Setup mocks
        mock_check_scraper.return_value = False
        mock_get_last_run.return_value = None
        
        # Call function
        result = check_health()
        
        # Assertions
        self.assertFalse(result)
        mock_send_alert.assert_called_once()
    
    @patch('src.health_check.check_health')
    def test_run_health_check_healthy(self, mock_check_health):
        """
        Test run_health_check function with healthy scraper.
        """
        # Setup mock
        mock_check_health.return_value = True
        
        # Call function
        result = run_health_check()
        
        # Assertions
        self.assertEqual(result, 0)
    
    @patch('src.health_check.check_health')
    def test_run_health_check_unhealthy(self, mock_check_health):
        """
        Test run_health_check function with unhealthy scraper.
        """
        # Setup mock
        mock_check_health.return_value = False
        
        # Call function
        result = run_health_check()
        
        # Assertions
        self.assertEqual(result, 1)
    
    @patch('src.health_check.check_health')
    def test_run_health_check_exception(self, mock_check_health):
        """
        Test run_health_check function with exception.
        """
        # Setup mock
        mock_check_health.side_effect = Exception("Test exception")
        
        # Call function
        result = run_health_check()
        
        # Assertions
        self.assertEqual(result, 1)

if __name__ == '__main__':
    unittest.main() 