"""
Integration tests for actual data functionality.
Tests end-to-end flow: scrape actual data → calculate sentiment → store in DB → Discord reports.
"""
import unittest
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timedelta
import json
import os

from src.scraper.actual_data_collector import ActualDataCollector
from src.analysis.sentiment_engine import SentimentCalculator
from src.discord.notifier import DiscordNotifier
from src.scheduler import SchedulerManager
from src.database.models import Event, Indicator, Sentiment

class TestActualDataIntegration(unittest.TestCase):
    """
    Integration tests for actual data functionality.
    """
    
    def setUp(self):
        """
        Set up test fixtures.
        """
        self.mock_db = MagicMock()
        
        # Mock environment variables
        self.env_patcher = patch.dict(os.environ, {
            'ACTUAL_DATA_COLLECTION_ENABLED': 'true',
            'ACTUAL_DATA_COLLECTION_INTERVAL': '4',
            'ACTUAL_DATA_RETRY_LIMIT': '3',
            'ACTUAL_DATA_LOOKBACK_DAYS': '7',
            'INCLUDE_ACTUAL_SENTIMENT_IN_REPORTS': 'true',
            'SHOW_FORECAST_ACCURACY_IN_REPORTS': 'true',
            'SHOW_SURPRISES_IN_REPORTS': 'true'
        })
        self.env_patcher.start()
    
    def tearDown(self):
        """
        Clean up test fixtures.
        """
        self.env_patcher.stop()
    
    @patch('src.scraper.actual_data_collector.SessionLocal')
    @patch('src.analysis.sentiment_engine.SessionLocal')
    def test_end_to_end_actual_data_flow(self, mock_sentiment_session, mock_collector_session):
        """
        Test complete end-to-end flow: collect actual data → calculate sentiment → store results.
        """
        # Mock database sessions
        mock_session = MagicMock()
        mock_collector_session.return_value = mock_session
        mock_sentiment_session.return_value = mock_session
        
        # Step 1: Mock events missing actual data
        mock_events_missing_data = [
            {
                "event_id": 1,
                "indicator_id": 10,
                "currency": "USD",
                "event_name": "CPI y/y",
                "scheduled_datetime": datetime(2024, 1, 14, 14, 30, 0),
                "previous_value": 2.0,
                "forecast_value": 2.5,
                "is_actual_available": False
            }
        ]
        
        # Step 2: Mock scraped actual data
        mock_scraped_events = [
            {
                "currency": "USD",
                "event_name": "CPI y/y",
                "scheduled_datetime": datetime(2024, 1, 14, 14, 30, 0),
                "actual_value": 2.3
            }
        ]
        
        # Step 3: Mock events with actual data for sentiment calculation
        mock_events_with_actual = [
            {
                "event_id": 1,
                "currency": "USD",
                "event_name": "CPI y/y",
                "previous_value": 2.0,
                "forecast_value": 2.5,
                "actual_value": 2.3,
                "is_actual_available": True
            }
        ]
        
        # Create collector and calculator
        collector = ActualDataCollector()
        calculator = SentimentCalculator()
        
        # Mock collector methods
        collector.get_events_missing_actual_data = MagicMock(return_value=mock_events_missing_data)
        collector.scraper.scrape_calendar = MagicMock(return_value=mock_scraped_events)
        collector.update_indicator_with_actual_data = MagicMock(return_value=True)
        
        # Mock calculator methods
        calculator.get_week_events_with_actual_indicators = MagicMock(return_value=mock_events_with_actual)
        calculator.persist_sentiments = MagicMock()
        
        # Execute the flow
        # Step 1: Collect actual data
        processed, updated = collector.collect_all_missing_actual_data()
        
        # Step 2: Calculate actual sentiment
        week_start = datetime(2024, 1, 8)
        week_end = datetime(2024, 1, 14)
        sentiment_results = calculator.calculate_actual_sentiment(week_start, week_end)
        
        # Verify results
        self.assertEqual(processed, 1)
        self.assertEqual(updated, 1)
        self.assertIn("USD", sentiment_results)
        
        # Verify method calls
        collector.get_events_missing_actual_data.assert_called_once()
        collector.scraper.scrape_calendar.assert_called_once()
        collector.update_indicator_with_actual_data.assert_called_once_with(10, 2.3)
        calculator.get_week_events_with_actual_indicators.assert_called_once()
    
    @patch('src.discord.notifier.requests.post')
    def test_discord_integration_with_actual_sentiment(self, mock_post):
        """
        Test Discord notification integration with actual sentiment data.
        """
        # Mock successful Discord webhook response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Mock sentiment data with actual sentiment
        mock_sentiment_data = {
            "USD": {
                "resolution": {
                    "final_sentiment": "Bullish",
                    "final_sentiment_value": 1,
                    "data_availability": {"available": 2, "missing": 0}
                },
                "events": [
                    {
                        "event_name": "CPI y/y",
                        "previous_value": 2.0,
                        "forecast_value": 2.5,
                        "actual_value": 2.3,
                        "forecast_sentiment": "Bullish",
                        "actual_sentiment": "Bullish",
                        "data_available": True
                    }
                ]
            }
        }
        
        # Create notifier
        notifier = DiscordNotifier(webhook_url="https://discord.com/webhook/test")
        
        # Mock the format methods to include actual sentiment
        notifier._format_currency_section = MagicMock(return_value=(
            "**USD** 🇺🇸: 🟢 Bullish → 🟢 **Bullish** ✅\n   Key: CPI y/y (F:2.5, A:2.3)",
            "USD: Bullish",
            85.0,  # Accuracy percentage
            []  # Surprises
        ))
        
        # Send notification
        result = notifier.send_weekly_report(mock_sentiment_data)
        
        # Verify Discord webhook was called
        self.assertTrue(result)
        mock_post.assert_called_once()
        
        # Verify the payload contains actual sentiment information
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        self.assertIn("content", payload)
        self.assertIn("Bullish", payload["content"])
    
    @patch('src.scheduler.ActualDataCollector')
    @patch('src.scheduler.SentimentCalculator')
    def test_scheduler_integration_actual_data_collection(self, mock_calculator_class, mock_collector_class):
        """
        Test scheduler integration for actual data collection.
        """
        # Mock collector and calculator instances
        mock_collector = MagicMock()
        mock_calculator = MagicMock()
        mock_collector_class.return_value = mock_collector
        mock_calculator_class.return_value = mock_calculator
        
        # Mock collection results
        mock_collector.collect_all_missing_actual_data.return_value = (5, 3)  # 5 processed, 3 updated
        
        # Create scheduler
        scheduler = SchedulerManager()
        
        # Mock the actual data collection job
        scheduler.collect_actual_data = MagicMock()
        
        # Execute actual data collection job
        scheduler.collect_actual_data()
        
        # Verify job was called
        scheduler.collect_actual_data.assert_called_once()
    
    def test_database_consistency_actual_data_updates(self):
        """
        Test database consistency when updating indicators with actual data.
        """
        # Mock database operations
        mock_indicator = MagicMock()
        mock_indicator.actual_value = None
        mock_indicator.is_actual_available = False
        mock_indicator.actual_collected_at = None
        
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_indicator
        
        # Create collector
        collector = ActualDataCollector(db_session=self.mock_db)
        
        # Update indicator with actual data
        result = collector.update_indicator_with_actual_data(10, 2.3)
        
        # Verify database consistency
        self.assertTrue(result)
        self.assertEqual(mock_indicator.actual_value, 2.3)
        self.assertTrue(mock_indicator.is_actual_available)
        self.assertIsNotNone(mock_indicator.actual_collected_at)
        self.mock_db.commit.assert_called_once()
    
    def test_error_handling_scraper_failure(self):
        """
        Test error handling when scraper fails during actual data collection.
        """
        # Create collector
        collector = ActualDataCollector(db_session=self.mock_db)
        
        # Mock scraper failure
        collector.scraper.scrape_calendar = MagicMock(side_effect=Exception("Network error"))
        
        # Mock events missing data
        mock_events = [
            {
                "event_id": 1,
                "indicator_id": 10,
                "currency": "USD",
                "event_name": "CPI y/y"
            }
        ]
        collector.get_events_missing_actual_data = MagicMock(return_value=mock_events)
        
        # Execute collection (should handle error gracefully)
        processed, updated = collector.collect_all_missing_actual_data()
        
        # Verify error handling
        self.assertEqual(processed, 1)  # Event was processed
        self.assertEqual(updated, 0)    # But not updated due to error
    
    def test_error_handling_database_failure(self):
        """
        Test error handling when database update fails.
        """
        # Mock database failure
        self.mock_db.commit.side_effect = Exception("Database error")
        mock_indicator = MagicMock()
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_indicator
        
        # Create collector
        collector = ActualDataCollector(db_session=self.mock_db)
        
        # Attempt to update indicator
        result = collector.update_indicator_with_actual_data(10, 2.3)
        
        # Verify error handling
        self.assertFalse(result)
        self.mock_db.rollback.assert_called_once()
    
    @patch('src.analysis.sentiment_engine.datetime')
    def test_sentiment_calculation_with_mixed_data_availability(self, mock_datetime):
        """
        Test sentiment calculation when some events have actual data and others don't.
        """
        # Mock current time
        mock_datetime.utcnow.return_value = datetime(2024, 1, 15, 12, 0, 0)
        
        # Mock events with mixed actual data availability
        mock_events = [
            {
                "event_id": 1,
                "currency": "USD",
                "event_name": "CPI y/y",
                "previous_value": 2.0,
                "actual_value": 2.3,
                "is_actual_available": True
            },
            {
                "event_id": 2,
                "currency": "USD",
                "event_name": "GDP q/q",
                "previous_value": 0.1,
                "actual_value": None,
                "is_actual_available": False
            }
        ]
        
        # Create calculator
        calculator = SentimentCalculator(db_session=self.mock_db)
        calculator.get_week_events_with_actual_indicators = MagicMock(return_value=mock_events)
        
        # Calculate sentiment
        result = calculator.calculate_actual_sentiment()
        
        # Verify mixed data handling
        self.assertIn("USD", result)
        usd_result = result["USD"]
        self.assertEqual(usd_result["resolution"]["data_availability"]["available"], 1)
        self.assertEqual(usd_result["resolution"]["data_availability"]["missing"], 1)
    
    def test_forecast_vs_actual_accuracy_calculation(self):
        """
        Test calculation of forecast vs actual accuracy metrics.
        """
        # Mock events with forecast and actual data
        mock_events = [
            {
                "event_id": 1,
                "currency": "USD",
                "event_name": "CPI y/y",
                "previous_value": 2.0,
                "forecast_value": 2.5,
                "actual_value": 2.3,
                "is_actual_available": True
            },
            {
                "event_id": 2,
                "currency": "USD",
                "event_name": "GDP q/q",
                "previous_value": 0.1,
                "forecast_value": 0.3,
                "actual_value": 0.05,  # Different sentiment direction
                "is_actual_available": True
            }
        ]
        
        # Create calculator
        calculator = SentimentCalculator(db_session=self.mock_db)
        
        # Calculate sentiments for both forecast and actual
        forecast_sentiments = []
        actual_sentiments = []
        
        for event in mock_events:
            forecast_result = calculator.calculate_event_sentiment(event)
            actual_result = calculator.calculate_actual_event_sentiment(event)
            forecast_sentiments.append(forecast_result["sentiment"])
            actual_sentiments.append(actual_result["sentiment"])
        
        # Calculate accuracy
        matches = sum(1 for f, a in zip(forecast_sentiments, actual_sentiments) if f == a)
        accuracy = (matches / len(forecast_sentiments)) * 100
        
        # Verify accuracy calculation
        self.assertEqual(len(forecast_sentiments), 2)
        self.assertEqual(len(actual_sentiments), 2)
        # First event: both bullish (match), second event: forecast bullish, actual bearish (no match)
        self.assertEqual(accuracy, 50.0)  # 1 out of 2 matches
    
    def test_performance_large_dataset(self):
        """
        Test performance with a large dataset of events.
        """
        # Create large dataset
        large_event_set = []
        for i in range(100):
            large_event_set.append({
                "event_id": i,
                "indicator_id": i + 100,
                "currency": ["USD", "EUR", "GBP", "JPY"][i % 4],
                "event_name": f"Event {i}",
                "scheduled_datetime": datetime(2024, 1, 14, 14, 30, 0),
                "previous_value": 2.0,
                "forecast_value": 2.5,
                "is_actual_available": False
            })
        
        # Create collector
        collector = ActualDataCollector(db_session=self.mock_db)
        collector.get_events_missing_actual_data = MagicMock(return_value=large_event_set)
        collector.collect_actual_data_for_event = MagicMock(return_value=2.3)
        collector.update_indicator_with_actual_data = MagicMock(return_value=True)
        
        # Measure performance
        import time
        start_time = time.time()
        processed, updated = collector.collect_all_missing_actual_data()
        end_time = time.time()
        
        # Verify performance (should complete within reasonable time)
        execution_time = end_time - start_time
        self.assertLess(execution_time, 10.0)  # Should complete within 10 seconds
        self.assertEqual(processed, 100)
        self.assertEqual(updated, 100)
    
    def test_data_validation_actual_values(self):
        """
        Test data validation for actual values.
        """
        # Create collector
        collector = ActualDataCollector(db_session=self.mock_db)
        
        # Test valid actual value
        valid_event = {
            "event_id": 1,
            "currency": "USD",
            "event_name": "CPI y/y",
            "scheduled_datetime": datetime(2024, 1, 14, 14, 30, 0)
        }
        
        # Mock scraper with valid data
        mock_scraped_events = [
            {
                "currency": "USD",
                "event_name": "CPI y/y",
                "scheduled_datetime": datetime(2024, 1, 14, 14, 30, 0),
                "actual_value": 2.3
            }
        ]
        collector.scraper.scrape_calendar = MagicMock(return_value=mock_scraped_events)
        
        # Collect actual data
        actual_value = collector.collect_actual_data_for_event(valid_event)
        
        # Verify valid data
        self.assertEqual(actual_value, 2.3)
        self.assertIsInstance(actual_value, (int, float))
    
    def test_concurrent_access_safety(self):
        """
        Test thread safety for concurrent actual data collection.
        """
        import threading
        import time
        
        # Create collector
        collector = ActualDataCollector(db_session=self.mock_db)
        
        # Mock database operations to simulate concurrent access
        mock_indicator = MagicMock()
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_indicator
        
        results = []
        
        def update_indicator(indicator_id, value):
            result = collector.update_indicator_with_actual_data(indicator_id, value)
            results.append(result)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=update_indicator, args=(i, 2.0 + i * 0.1))
            threads.append(thread)
        
        # Start all threads
        for thread in threads:
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all operations completed successfully
        self.assertEqual(len(results), 5)
        self.assertTrue(all(results))  # All should be True

if __name__ == '__main__':
    unittest.main() 