"""
Tests for the run_analysis module.
"""
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import argparse

from src.run_analysis import run_analysis, parse_date, run_analysis_cli

class TestRunAnalysis(unittest.TestCase):
    """
    Tests for the run_analysis module.
    """
    
    @patch('src.run_analysis.SentimentCalculator')
    @patch('src.run_analysis.get_db_session')
    def test_run_analysis_success(self, mock_get_db_session, mock_calculator_class):
        """
        Test run_analysis function with successful execution.
        """
        # Setup mocks
        mock_db = MagicMock()
        mock_get_db_session.return_value.__enter__.return_value = mock_db
        
        mock_calculator = MagicMock()
        mock_calculator_class.return_value = mock_calculator
        
        mock_sentiments = {
            "USD": {"resolution": {"final_sentiment": "Bullish", "reason": "Test reason"}},
            "EUR": {"resolution": {"final_sentiment": "Bearish", "reason": "Test reason"}}
        }
        mock_calculator.calculate_weekly_sentiments.return_value = mock_sentiments
        
        # Call function
        result = run_analysis()
        
        # Assertions
        self.assertEqual(result, 0)
        mock_calculator_class.assert_called_once_with(db_session=mock_db)
        mock_calculator.calculate_weekly_sentiments.assert_called_once_with(None, None)
    
    @patch('src.run_analysis.SentimentCalculator')
    @patch('src.run_analysis.get_db_session')
    def test_run_analysis_no_sentiments(self, mock_get_db_session, mock_calculator_class):
        """
        Test run_analysis function with no sentiments returned.
        """
        # Setup mocks
        mock_db = MagicMock()
        mock_get_db_session.return_value.__enter__.return_value = mock_db
        
        mock_calculator = MagicMock()
        mock_calculator_class.return_value = mock_calculator
        mock_calculator.calculate_weekly_sentiments.return_value = {}
        
        # Call function
        result = run_analysis()
        
        # Assertions
        self.assertEqual(result, 1)
    
    @patch('src.run_analysis.SentimentCalculator')
    @patch('src.run_analysis.get_db_session')
    def test_run_analysis_exception(self, mock_get_db_session, mock_calculator_class):
        """
        Test run_analysis function with exception.
        """
        # Setup mocks
        mock_db = MagicMock()
        mock_get_db_session.return_value.__enter__.return_value = mock_db
        
        mock_calculator = MagicMock()
        mock_calculator_class.return_value = mock_calculator
        mock_calculator.calculate_weekly_sentiments.side_effect = Exception("Test exception")
        
        # Call function
        result = run_analysis()
        
        # Assertions
        self.assertEqual(result, 1)
    
    @patch('src.run_analysis.SentimentCalculator')
    @patch('src.run_analysis.get_db_session')
    def test_run_analysis_with_dates(self, mock_get_db_session, mock_calculator_class):
        """
        Test run_analysis function with specific dates.
        """
        # Setup mocks
        mock_db = MagicMock()
        mock_get_db_session.return_value.__enter__.return_value = mock_db
        
        mock_calculator = MagicMock()
        mock_calculator_class.return_value = mock_calculator
        
        mock_sentiments = {
            "USD": {"resolution": {"final_sentiment": "Bullish", "reason": "Test reason"}}
        }
        mock_calculator.calculate_weekly_sentiments.return_value = mock_sentiments
        
        # Call function with specific dates
        week_start = datetime(2024, 1, 8)
        week_end = datetime(2024, 1, 14)
        result = run_analysis(week_start, week_end)
        
        # Assertions
        self.assertEqual(result, 0)
        mock_calculator.calculate_weekly_sentiments.assert_called_once_with(week_start, week_end)
    
    def test_parse_date_valid(self):
        """
        Test parse_date function with valid date.
        """
        result = parse_date("2024-01-15")
        expected = datetime(2024, 1, 15)
        self.assertEqual(result, expected)
    
    def test_parse_date_invalid(self):
        """
        Test parse_date function with invalid date.
        """
        with self.assertRaises(argparse.ArgumentTypeError):
            parse_date("invalid-date")
    
    @patch('src.run_analysis.run_analysis')
    @patch('src.run_analysis.sys.exit')
    def test_run_analysis_cli_current_week(self, mock_exit, mock_run_analysis):
        """
        Test run_analysis_cli function with current week.
        """
        mock_run_analysis.return_value = 0
        
        with patch('sys.argv', ['run_analysis.py', '--current-week']):
            run_analysis_cli()
        
        mock_run_analysis.assert_called_once_with(None, None)
        mock_exit.assert_called_once_with(0)
    
    @patch('src.run_analysis.run_analysis')
    @patch('src.run_analysis.sys.exit')
    def test_run_analysis_cli_with_dates(self, mock_exit, mock_run_analysis):
        """
        Test run_analysis_cli function with specific dates.
        """
        mock_run_analysis.return_value = 0
        
        with patch('sys.argv', ['run_analysis.py', '--week-start', '2024-01-08', '--week-end', '2024-01-14']):
            run_analysis_cli()
        
        # Check that run_analysis was called with datetime objects
        call_args = mock_run_analysis.call_args[0]
        self.assertEqual(call_args[0].year, 2024)
        self.assertEqual(call_args[0].month, 1)
        self.assertEqual(call_args[0].day, 8)
        mock_exit.assert_called_once_with(0)

if __name__ == '__main__':
    unittest.main() 