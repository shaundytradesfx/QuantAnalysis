"""
Tests for the actual data collector functionality.
"""
import unittest
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timedelta
import json

from src.scraper.actual_data_collector import ActualDataCollector
from src.database.models import Event, Indicator

class TestActualDataCollector(unittest.TestCase):
    """
    Tests for the ActualDataCollector class.
    """
    
    def setUp(self):
        """
        Set up test fixtures.
        """
        self.mock_db = MagicMock()
        self.collector = ActualDataCollector(db_session=self.mock_db, lookback_days=7, retry_limit=3)
    
    def test_init_with_session(self):
        """
        Test ActualDataCollector initialization with provided session.
        """
        collector = ActualDataCollector(db_session=self.mock_db, lookback_days=5, retry_limit=2)
        self.assertEqual(collector.db, self.mock_db)
        self.assertEqual(collector.lookback_days, 5)
        self.assertEqual(collector.retry_limit, 2)
        self.assertFalse(collector.close_db_on_exit)
    
    @patch('src.scraper.actual_data_collector.SessionLocal')
    def test_init_without_session(self, mock_session_local):
        """
        Test ActualDataCollector initialization without provided session.
        """
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        
        collector = ActualDataCollector(lookback_days=10, retry_limit=5)
        self.assertEqual(collector.db, mock_session)
        self.assertEqual(collector.lookback_days, 10)
        self.assertEqual(collector.retry_limit, 5)
        self.assertTrue(collector.close_db_on_exit)
    
    @patch('src.scraper.actual_data_collector.datetime')
    def test_get_events_missing_actual_data(self, mock_datetime):
        """
        Test getting events that are missing actual data.
        """
        # Mock current time
        current_time = datetime(2024, 1, 15, 12, 0, 0)
        mock_datetime.datetime.utcnow.return_value = current_time
        
        # Mock database query result
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.event_id = 1
        mock_row.indicator_id = 10
        mock_row.currency = "USD"
        mock_row.event_name = "CPI y/y"
        mock_row.scheduled_datetime = datetime(2024, 1, 14, 14, 30, 0)
        mock_row.impact_level = "High"
        mock_row.previous_value = 2.0
        mock_row.forecast_value = 2.5
        mock_row.is_actual_available = False
        mock_row.timestamp_collected = datetime(2024, 1, 14, 10, 0, 0)
        
        mock_result.__iter__ = lambda self: iter([mock_row])
        self.mock_db.execute.return_value = mock_result
        
        # Call the method
        events = self.collector.get_events_missing_actual_data()
        
        # Verify results
        self.assertEqual(len(events), 1)
        event = events[0]
        self.assertEqual(event["event_id"], 1)
        self.assertEqual(event["currency"], "USD")
        self.assertEqual(event["event_name"], "CPI y/y")
        self.assertFalse(event["is_actual_available"])
        
        # Verify database query was called with correct parameters
        self.mock_db.execute.assert_called_once()
        call_args = self.mock_db.execute.call_args
        self.assertIn("cutoff_date", call_args[1])
        self.assertIn("current_time", call_args[1])
    
    @patch.object(ActualDataCollector, '_events_match')
    @patch.object(ActualDataCollector, '_datetimes_match')
    def test_collect_actual_data_for_event_success(self, mock_datetimes_match, mock_events_match):
        """
        Test successful collection of actual data for an event.
        """
        # Mock scraper
        mock_scraped_events = [
            {
                "currency": "USD",
                "event_name": "CPI y/y",
                "scheduled_datetime": datetime(2024, 1, 14, 14, 30, 0),
                "actual_value": 2.3
            }
        ]
        self.collector.scraper.scrape_calendar = MagicMock(return_value=mock_scraped_events)
        
        # Mock matching methods
        mock_events_match.return_value = True
        mock_datetimes_match.return_value = True
        
        # Test event
        event = {
            "event_id": 1,
            "currency": "USD",
            "event_name": "CPI y/y",
            "scheduled_datetime": datetime(2024, 1, 14, 14, 30, 0)
        }
        
        # Call the method
        actual_value = self.collector.collect_actual_data_for_event(event)
        
        # Verify results
        self.assertEqual(actual_value, 2.3)
        self.collector.scraper.scrape_calendar.assert_called_once()
        mock_events_match.assert_called_once_with("CPI y/y", "CPI y/y")
        mock_datetimes_match.assert_called_once()
    
    def test_collect_actual_data_for_event_no_match(self):
        """
        Test collection when no matching event is found.
        """
        # Mock scraper with non-matching events
        mock_scraped_events = [
            {
                "currency": "EUR",
                "event_name": "GDP q/q",
                "scheduled_datetime": datetime(2024, 1, 14, 14, 30, 0),
                "actual_value": 1.5
            }
        ]
        self.collector.scraper.scrape_calendar = MagicMock(return_value=mock_scraped_events)
        
        # Test event
        event = {
            "event_id": 1,
            "currency": "USD",
            "event_name": "CPI y/y",
            "scheduled_datetime": datetime(2024, 1, 14, 14, 30, 0)
        }
        
        # Call the method
        actual_value = self.collector.collect_actual_data_for_event(event)
        
        # Verify results
        self.assertIsNone(actual_value)
    
    def test_collect_actual_data_for_event_scraper_error(self):
        """
        Test collection when scraper fails.
        """
        # Mock scraper to raise exception
        self.collector.scraper.scrape_calendar = MagicMock(side_effect=Exception("Scraper error"))
        
        # Test event
        event = {
            "event_id": 1,
            "currency": "USD",
            "event_name": "CPI y/y",
            "scheduled_datetime": datetime(2024, 1, 14, 14, 30, 0)
        }
        
        # Call the method
        actual_value = self.collector.collect_actual_data_for_event(event)
        
        # Verify results
        self.assertIsNone(actual_value)
    
    def test_events_match_exact(self):
        """
        Test exact event name matching.
        """
        result = self.collector._events_match("CPI y/y", "CPI y/y")
        self.assertTrue(result)
    
    def test_events_match_case_insensitive(self):
        """
        Test case insensitive event name matching.
        """
        result = self.collector._events_match("CPI Y/Y", "cpi y/y")
        self.assertTrue(result)
    
    def test_events_match_with_variations(self):
        """
        Test event name matching with common variations.
        """
        result = self.collector._events_match("CPI m/m", "CPI mom")
        self.assertTrue(result)
        
        result = self.collector._events_match("GDP y/y", "GDP yoy")
        self.assertTrue(result)
    
    def test_events_match_partial(self):
        """
        Test partial event name matching.
        """
        result = self.collector._events_match("CPI", "CPI y/y Final")
        self.assertTrue(result)
        
        result = self.collector._events_match("Unemployment Rate", "Unemployment")
        self.assertTrue(result)
    
    def test_events_match_no_match(self):
        """
        Test event name matching when names don't match.
        """
        result = self.collector._events_match("CPI y/y", "GDP q/q")
        self.assertFalse(result)
    
    def test_events_match_empty_names(self):
        """
        Test event name matching with empty names.
        """
        result = self.collector._events_match("", "CPI y/y")
        self.assertFalse(result)
        
        result = self.collector._events_match("CPI y/y", "")
        self.assertFalse(result)
        
        result = self.collector._events_match(None, "CPI y/y")
        self.assertFalse(result)
    
    def test_datetimes_match_exact(self):
        """
        Test exact datetime matching.
        """
        dt1 = datetime(2024, 1, 14, 14, 30, 0)
        dt2 = datetime(2024, 1, 14, 14, 30, 0)
        
        result = self.collector._datetimes_match(dt1, dt2)
        self.assertTrue(result)
    
    def test_datetimes_match_within_window(self):
        """
        Test datetime matching within acceptable window.
        """
        dt1 = datetime(2024, 1, 14, 14, 30, 0)
        dt2 = datetime(2024, 1, 14, 14, 35, 0)  # 5 minutes difference
        
        result = self.collector._datetimes_match(dt1, dt2)
        self.assertTrue(result)
    
    def test_datetimes_match_outside_window(self):
        """
        Test datetime matching outside acceptable window.
        """
        dt1 = datetime(2024, 1, 14, 14, 30, 0)
        dt2 = datetime(2024, 1, 14, 16, 30, 0)  # 2 hours difference
        
        result = self.collector._datetimes_match(dt1, dt2)
        self.assertFalse(result)
    
    def test_datetimes_match_none_datetime(self):
        """
        Test datetime matching with None datetime.
        """
        dt1 = datetime(2024, 1, 14, 14, 30, 0)
        
        result = self.collector._datetimes_match(dt1, None)
        self.assertFalse(result)
    
    def test_update_indicator_with_actual_data_success(self):
        """
        Test successful update of indicator with actual data.
        """
        # Mock database operations
        mock_indicator = MagicMock()
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_indicator
        
        # Call the method
        result = self.collector.update_indicator_with_actual_data(10, 2.3)
        
        # Verify results
        self.assertTrue(result)
        self.assertEqual(mock_indicator.actual_value, 2.3)
        self.assertTrue(mock_indicator.is_actual_available)
        self.assertIsNotNone(mock_indicator.actual_collected_at)
        self.mock_db.commit.assert_called_once()
    
    def test_update_indicator_with_actual_data_not_found(self):
        """
        Test update when indicator is not found.
        """
        # Mock database operations
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        # Call the method
        result = self.collector.update_indicator_with_actual_data(10, 2.3)
        
        # Verify results
        self.assertFalse(result)
        self.mock_db.commit.assert_not_called()
    
    def test_update_indicator_with_actual_data_database_error(self):
        """
        Test update when database error occurs.
        """
        # Mock database operations to raise exception
        self.mock_db.commit.side_effect = Exception("Database error")
        mock_indicator = MagicMock()
        self.mock_db.query.return_value.filter.return_value.first.return_value = mock_indicator
        
        # Call the method
        result = self.collector.update_indicator_with_actual_data(10, 2.3)
        
        # Verify results
        self.assertFalse(result)
        self.mock_db.rollback.assert_called_once()
    
    @patch.object(ActualDataCollector, 'get_events_missing_actual_data')
    @patch.object(ActualDataCollector, 'collect_actual_data_for_event')
    @patch.object(ActualDataCollector, 'update_indicator_with_actual_data')
    def test_collect_all_missing_actual_data_success(self, mock_update, mock_collect, mock_get_events):
        """
        Test successful collection of all missing actual data.
        """
        # Mock events missing actual data
        mock_events = [
            {
                "event_id": 1,
                "indicator_id": 10,
                "currency": "USD",
                "event_name": "CPI y/y"
            },
            {
                "event_id": 2,
                "indicator_id": 11,
                "currency": "EUR",
                "event_name": "GDP q/q"
            }
        ]
        mock_get_events.return_value = mock_events
        
        # Mock successful data collection
        mock_collect.side_effect = [2.3, 1.5]  # Actual values for both events
        mock_update.return_value = True
        
        # Call the method
        processed, updated = self.collector.collect_all_missing_actual_data()
        
        # Verify results
        self.assertEqual(processed, 2)
        self.assertEqual(updated, 2)
        
        # Verify method calls
        mock_get_events.assert_called_once()
        self.assertEqual(mock_collect.call_count, 2)
        self.assertEqual(mock_update.call_count, 2)
        mock_update.assert_has_calls([call(10, 2.3), call(11, 1.5)])
    
    @patch.object(ActualDataCollector, 'get_events_missing_actual_data')
    @patch.object(ActualDataCollector, 'collect_actual_data_for_event')
    @patch.object(ActualDataCollector, 'update_indicator_with_actual_data')
    def test_collect_all_missing_actual_data_partial_success(self, mock_update, mock_collect, mock_get_events):
        """
        Test collection when some events have no actual data available.
        """
        # Mock events missing actual data
        mock_events = [
            {
                "event_id": 1,
                "indicator_id": 10,
                "currency": "USD",
                "event_name": "CPI y/y"
            },
            {
                "event_id": 2,
                "indicator_id": 11,
                "currency": "EUR",
                "event_name": "GDP q/q"
            }
        ]
        mock_get_events.return_value = mock_events
        
        # Mock partial data collection (first succeeds, second fails)
        mock_collect.side_effect = [2.3, None]
        mock_update.return_value = True
        
        # Call the method
        processed, updated = self.collector.collect_all_missing_actual_data()
        
        # Verify results
        self.assertEqual(processed, 2)
        self.assertEqual(updated, 1)  # Only one was updated
        
        # Verify method calls
        mock_get_events.assert_called_once()
        self.assertEqual(mock_collect.call_count, 2)
        self.assertEqual(mock_update.call_count, 1)  # Only called for successful collection
        mock_update.assert_called_once_with(10, 2.3)
    
    @patch.object(ActualDataCollector, 'get_events_missing_actual_data')
    def test_collect_all_missing_actual_data_no_events(self, mock_get_events):
        """
        Test collection when no events are missing actual data.
        """
        # Mock no events missing actual data
        mock_get_events.return_value = []
        
        # Call the method
        processed, updated = self.collector.collect_all_missing_actual_data()
        
        # Verify results
        self.assertEqual(processed, 0)
        self.assertEqual(updated, 0)
        
        # Verify method calls
        mock_get_events.assert_called_once()
    
    def test_context_manager_with_session(self):
        """
        Test context manager when session is provided.
        """
        collector = ActualDataCollector(db_session=self.mock_db)
        
        with collector as c:
            self.assertEqual(c, collector)
            self.assertEqual(c.db, self.mock_db)
        
        # Should not close the session since it was provided
        self.mock_db.close.assert_not_called()
    
    @patch('src.scraper.actual_data_collector.SessionLocal')
    def test_context_manager_without_session(self, mock_session_local):
        """
        Test context manager when no session is provided.
        """
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        
        collector = ActualDataCollector()
        
        with collector as c:
            self.assertEqual(c, collector)
            self.assertEqual(c.db, mock_session)
        
        # Should close the session since it was created internally
        mock_session.close.assert_called_once()

if __name__ == '__main__':
    unittest.main() 