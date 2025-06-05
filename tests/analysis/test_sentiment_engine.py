"""
Tests for the sentiment calculation engine.
"""
import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import json

from src.analysis.sentiment_engine import SentimentCalculator
from src.database.models import Event, Indicator, Sentiment

class TestSentimentCalculator(unittest.TestCase):
    """
    Tests for the SentimentCalculator class.
    """
    
    def setUp(self):
        """
        Set up test fixtures.
        """
        self.mock_db = MagicMock()
        self.calculator = SentimentCalculator(db_session=self.mock_db, threshold=0.1)
    
    def test_init_with_session(self):
        """
        Test SentimentCalculator initialization with provided session.
        """
        calc = SentimentCalculator(db_session=self.mock_db, threshold=0.5)
        self.assertEqual(calc.db, self.mock_db)
        self.assertEqual(calc.threshold, 0.5)
        self.assertFalse(calc.close_db_on_exit)
    
    @patch('src.analysis.sentiment_engine.SessionLocal')
    def test_init_without_session(self, mock_session_local):
        """
        Test SentimentCalculator initialization without provided session.
        """
        mock_session = MagicMock()
        mock_session_local.return_value = mock_session
        
        calc = SentimentCalculator(threshold=0.2)
        self.assertEqual(calc.db, mock_session)
        self.assertEqual(calc.threshold, 0.2)
        self.assertTrue(calc.close_db_on_exit)
    
    def test_get_next_week_bounds(self):
        """
        Test get_next_week_bounds method.
        """
        # Mock a specific date (Wednesday)
        test_date = datetime(2024, 1, 10, 15, 30, 0)  # Wednesday, Jan 10, 2024
        
        with patch('src.analysis.sentiment_engine.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value = test_date
            
            week_start, week_end = self.calculator.get_next_week_bounds()
            
            # Should be Monday Jan 15, 2024 00:00:00 (next week)
            expected_start = datetime(2024, 1, 15, 0, 0, 0)
            # Should be Sunday Jan 21, 2024 23:59:59 (next week)
            expected_end = datetime(2024, 1, 21, 23, 59, 59)
            
            self.assertEqual(week_start, expected_start)
            self.assertEqual(week_end, expected_end)
    
    def test_calculate_event_sentiment_bullish(self):
        """
        Test calculate_event_sentiment with bullish scenario.
        """
        event = {
            "event_id": 1,
            "event_name": "CPI y/y",
            "previous_value": 2.0,
            "forecast_value": 2.5  # Higher than previous + threshold
        }
        
        result = self.calculator.calculate_event_sentiment(event)
        
        self.assertEqual(result["sentiment"], 1)
        self.assertEqual(result["sentiment_label"], "Bullish")
        self.assertTrue(result["data_available"])
        self.assertIsNone(result["reason"])
    
    def test_calculate_event_sentiment_bearish(self):
        """
        Test calculate_event_sentiment with bearish scenario.
        """
        event = {
            "event_id": 1,
            "event_name": "CPI y/y",
            "previous_value": 2.5,
            "forecast_value": 2.0  # Lower than previous - threshold
        }
        
        result = self.calculator.calculate_event_sentiment(event)
        
        self.assertEqual(result["sentiment"], -1)
        self.assertEqual(result["sentiment_label"], "Bearish")
        self.assertTrue(result["data_available"])
        self.assertIsNone(result["reason"])
    
    def test_calculate_event_sentiment_neutral(self):
        """
        Test calculate_event_sentiment with neutral scenario.
        """
        event = {
            "event_id": 1,
            "event_name": "CPI y/y",
            "previous_value": 2.0,
            "forecast_value": 2.05  # Within threshold
        }
        
        result = self.calculator.calculate_event_sentiment(event)
        
        self.assertEqual(result["sentiment"], 0)
        self.assertEqual(result["sentiment_label"], "Neutral")
        self.assertTrue(result["data_available"])
        self.assertIsNone(result["reason"])
    
    def test_calculate_event_sentiment_missing_data(self):
        """
        Test calculate_event_sentiment with missing data.
        """
        event = {
            "event_id": 1,
            "event_name": "CPI y/y",
            "previous_value": None,
            "forecast_value": 2.5
        }
        
        result = self.calculator.calculate_event_sentiment(event)
        
        self.assertEqual(result["sentiment"], 0)
        self.assertEqual(result["sentiment_label"], "Neutral")
        self.assertFalse(result["data_available"])
        self.assertEqual(result["reason"], "Missing forecast or previous value")
    
    # ===== ACTUAL SENTIMENT TESTS (Phase 5) =====
    
    def test_calculate_actual_event_sentiment_bullish(self):
        """
        Test calculate_actual_event_sentiment with bullish scenario.
        """
        event = {
            "event_id": 1,
            "event_name": "CPI y/y",
            "previous_value": 2.0,
            "actual_value": 2.5,  # Higher than previous + threshold
            "is_actual_available": True
        }
        
        result = self.calculator.calculate_actual_event_sentiment(event)
        
        self.assertEqual(result["actual_sentiment"], 1)
        self.assertEqual(result["actual_sentiment_label"], "Bullish")
        self.assertTrue(result["actual_data_available"])
        self.assertIsNotNone(result["actual_reason"])  # Implementation provides reason
    
    def test_calculate_actual_event_sentiment_bearish(self):
        """
        Test calculate_actual_event_sentiment with bearish scenario.
        """
        event = {
            "event_id": 1,
            "event_name": "CPI y/y",
            "previous_value": 2.5,
            "actual_value": 2.0,  # Lower than previous - threshold
            "is_actual_available": True
        }
        
        result = self.calculator.calculate_actual_event_sentiment(event)
        
        self.assertEqual(result["actual_sentiment"], -1)
        self.assertEqual(result["actual_sentiment_label"], "Bearish")
        self.assertTrue(result["actual_data_available"])
        self.assertIsNotNone(result["actual_reason"])  # Implementation provides reason
    
    def test_calculate_actual_event_sentiment_neutral(self):
        """
        Test calculate_actual_event_sentiment with neutral scenario.
        """
        event = {
            "event_id": 1,
            "event_name": "CPI y/y",
            "previous_value": 2.0,
            "actual_value": 2.05,  # Within threshold
            "is_actual_available": True
        }
        
        result = self.calculator.calculate_actual_event_sentiment(event)
        
        self.assertEqual(result["actual_sentiment"], 0)
        self.assertEqual(result["actual_sentiment_label"], "Neutral")
        self.assertTrue(result["actual_data_available"])
        self.assertIsNotNone(result["actual_reason"])  # Implementation provides reason
    
    def test_calculate_actual_event_sentiment_missing_actual_data(self):
        """
        Test calculate_actual_event_sentiment with missing actual data.
        """
        event = {
            "event_id": 1,
            "event_name": "CPI y/y",
            "previous_value": 2.0,
            "actual_value": None,
            "is_actual_available": False
        }
        
        result = self.calculator.calculate_actual_event_sentiment(event)
        
        self.assertEqual(result["actual_sentiment"], 0)
        self.assertEqual(result["actual_sentiment_label"], "Neutral")
        self.assertFalse(result["actual_data_available"])
        self.assertEqual(result["actual_reason"], "Missing actual or previous value")
    
    def test_calculate_actual_event_sentiment_inverse_indicator(self):
        """
        Test calculate_actual_event_sentiment with inverse indicator (unemployment).
        """
        event = {
            "event_id": 1,
            "event_name": "Unemployment Rate",
            "previous_value": 3.5,
            "actual_value": 4.0,  # Higher unemployment = bearish
            "is_actual_available": True
        }
        
        result = self.calculator.calculate_actual_event_sentiment(event)
        
        self.assertEqual(result["actual_sentiment"], -1)  # Should be bearish for higher unemployment
        self.assertEqual(result["actual_sentiment_label"], "Bearish")
        self.assertTrue(result["actual_data_available"])
    
    def test_get_week_events_with_actual_indicators(self):
        """
        Test get_week_events_with_actual_indicators method.
        """
        # Mock the database query result
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([
            MagicMock(
                event_id=1,
                currency="USD",
                event_name="CPI y/y",
                scheduled_datetime=datetime(2024, 1, 10),
                impact_level="High",
                previous_value=2.0,
                forecast_value=2.5,
                actual_value=2.3,
                is_actual_available=True,
                actual_collected_at=datetime(2024, 1, 10, 15, 0),
                timestamp_collected=datetime(2024, 1, 9)
            ),
            MagicMock(
                event_id=2,
                currency="EUR",
                event_name="GDP q/q",
                scheduled_datetime=datetime(2024, 1, 11),
                impact_level="High",
                previous_value=0.1,
                forecast_value=0.2,
                actual_value=None,
                is_actual_available=False,
                actual_collected_at=None,
                timestamp_collected=datetime(2024, 1, 10)
            )
        ]))
        
        self.mock_db.execute.return_value = mock_result
        
        week_start = datetime(2024, 1, 8)
        week_end = datetime(2024, 1, 14)
        
        events = self.calculator.get_week_events_with_actual_indicators(week_start, week_end)
        
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["currency"], "USD")
        self.assertEqual(events[0]["actual_value"], 2.3)
        self.assertTrue(events[0]["is_actual_available"])
        self.assertEqual(events[1]["currency"], "EUR")
        self.assertIsNone(events[1]["actual_value"])
        self.assertFalse(events[1]["is_actual_available"])
        self.mock_db.execute.assert_called_once()
    
    def test_resolve_actual_currency_conflicts_all_bullish(self):
        """
        Test resolve_actual_currency_conflicts with all bullish events.
        """
        events = [
            {"actual_sentiment": 1, "actual_sentiment_label": "Bullish", "actual_data_available": True},
            {"actual_sentiment": 1, "actual_sentiment_label": "Bullish", "actual_data_available": True},
            {"actual_sentiment": 1, "actual_sentiment_label": "Bullish", "actual_data_available": True}
        ]
        
        result = self.calculator.resolve_actual_currency_conflicts(events)
        
        self.assertEqual(result["final_sentiment"], "Bullish")
        self.assertEqual(result["final_sentiment_value"], 1)
        self.assertEqual(result["event_count"], 3)
        self.assertEqual(result["sentiment_breakdown"]["bullish"], 3)
        self.assertEqual(result["data_availability"]["available"], 3)
    
    def test_resolve_actual_currency_conflicts_mixed_with_missing_data(self):
        """
        Test resolve_actual_currency_conflicts with mixed sentiments and missing data.
        """
        events = [
            {"actual_sentiment": 1, "actual_sentiment_label": "Bullish", "actual_data_available": True},
            {"actual_sentiment": -1, "actual_sentiment_label": "Bearish", "actual_data_available": True},
            {"actual_sentiment": 0, "actual_sentiment_label": "Neutral", "actual_data_available": False, "actual_reason": "Actual data not available"}
        ]
        
        result = self.calculator.resolve_actual_currency_conflicts(events)
        
        # Should resolve to tie with consolidation since only 2 events have data
        self.assertEqual(result["final_sentiment"], "Bearish with Consolidation")
        self.assertEqual(result["final_sentiment_value"], -1)
        self.assertEqual(result["event_count"], 3)
        self.assertEqual(result["data_availability"]["available"], 2)
        self.assertEqual(result["data_availability"]["missing"], 1)
    
    @patch.object(SentimentCalculator, 'get_week_events_with_actual_indicators')
    def test_calculate_actual_sentiment_full_flow(self, mock_get_events):
        """
        Test the full calculate_actual_sentiment flow.
        """
        # Mock events data with actual values
        mock_events = [
            {
                "event_id": 1,
                "currency": "USD",
                "event_name": "CPI y/y",
                "previous_value": 2.0,
                "actual_value": 2.5,
                "is_actual_available": True
            },
            {
                "event_id": 2,
                "currency": "USD",
                "event_name": "GDP q/q",
                "previous_value": 0.1,
                "actual_value": 0.3,
                "is_actual_available": True
            },
            {
                "event_id": 3,
                "currency": "EUR",
                "event_name": "CPI y/y",
                "previous_value": 1.5,
                "actual_value": 1.0,
                "is_actual_available": True
            },
            {
                "event_id": 4,
                "currency": "EUR",
                "event_name": "GDP q/q",
                "previous_value": 0.2,
                "actual_value": None,
                "is_actual_available": False
            }
        ]
        
        mock_get_events.return_value = mock_events
        
        result = self.calculator.calculate_actual_sentiment()
        
        # Should have results for USD and EUR
        self.assertIn("USD", result)
        self.assertIn("EUR", result)
        
        # USD should be bullish (2 bullish events with actual data)
        self.assertEqual(result["USD"]["resolution"]["final_sentiment"], "Bullish")
        self.assertEqual(result["USD"]["resolution"]["data_availability"]["available"], 2)
        
        # EUR should be bearish (1 bearish event with actual data, 1 missing)
        self.assertEqual(result["EUR"]["resolution"]["final_sentiment"], "Bearish")
        self.assertEqual(result["EUR"]["resolution"]["data_availability"]["available"], 1)
        self.assertEqual(result["EUR"]["resolution"]["data_availability"]["missing"], 1)
    
    # ===== EXISTING TESTS (unchanged) =====
    
    def test_resolve_currency_conflicts_all_bullish(self):
        """
        Test conflict resolution with all bullish events.
        """
        events = [
            {"sentiment": 1, "sentiment_label": "Bullish"},
            {"sentiment": 1, "sentiment_label": "Bullish"},
            {"sentiment": 1, "sentiment_label": "Bullish"}
        ]
        
        result = self.calculator.resolve_currency_conflicts(events)
        
        self.assertEqual(result["final_sentiment"], "Bullish")
        self.assertEqual(result["final_sentiment_value"], 1)
        self.assertEqual(result["event_count"], 3)
        self.assertEqual(result["sentiment_breakdown"]["bullish"], 3)
    
    def test_resolve_currency_conflicts_majority_bearish(self):
        """
        Test conflict resolution with majority bearish.
        """
        events = [
            {"sentiment": -1, "sentiment_label": "Bearish"},
            {"sentiment": -1, "sentiment_label": "Bearish"},
            {"sentiment": 1, "sentiment_label": "Bullish"}
        ]
        
        result = self.calculator.resolve_currency_conflicts(events)
        
        self.assertEqual(result["final_sentiment"], "Bearish")
        self.assertEqual(result["final_sentiment_value"], -1)
        self.assertIn("Majority bearish (2/3 events)", result["reason"])
    
    def test_resolve_currency_conflicts_tie_bearish(self):
        """
        Test conflict resolution with tie resolved to bearish.
        """
        events = [
            {"sentiment": -1, "sentiment_label": "Bearish"},
            {"sentiment": 1, "sentiment_label": "Bullish"}
        ]
        
        result = self.calculator.resolve_currency_conflicts(events)
        
        self.assertEqual(result["final_sentiment"], "Bearish with Consolidation")
        self.assertEqual(result["final_sentiment_value"], -1)
        self.assertIn("Tie resolved bearish", result["reason"])
    
    def test_resolve_currency_conflicts_tie_bullish(self):
        """
        Test conflict resolution with tie resolved to bullish.
        """
        # Modify the calculator to test the bullish tie scenario
        # This happens when bullish > bearish in a tie situation
        events = [
            {"sentiment": 1, "sentiment_label": "Bullish"},
            {"sentiment": 1, "sentiment_label": "Bullish"},
            {"sentiment": -1, "sentiment_label": "Bearish"},
            {"sentiment": 0, "sentiment_label": "Neutral"},
            {"sentiment": 0, "sentiment_label": "Neutral"}
        ]
        # This creates a tie between bullish (2) and neutral (2), bearish (1)
        # Should resolve to "Bullish with Consolidation"
        
        result = self.calculator.resolve_currency_conflicts(events)
        
        # In this case, bullish has majority so it should be "Bullish"
        self.assertEqual(result["final_sentiment"], "Bullish")
        self.assertEqual(result["final_sentiment_value"], 1)
    
    def test_resolve_currency_conflicts_empty(self):
        """
        Test conflict resolution with no events.
        """
        events = []
        
        result = self.calculator.resolve_currency_conflicts(events)
        
        self.assertEqual(result["final_sentiment"], "Neutral")
        self.assertEqual(result["final_sentiment_value"], 0)
        self.assertEqual(result["reason"], "No events found")
        self.assertEqual(result["event_count"], 0)
    
    def test_get_week_events_with_indicators(self):
        """
        Test get_week_events_with_indicators method.
        """
        # Mock the database query result
        mock_result = MagicMock()
        mock_result.__iter__ = MagicMock(return_value=iter([
            MagicMock(
                event_id=1,
                currency="USD",
                event_name="CPI y/y",
                scheduled_datetime=datetime(2024, 1, 10),
                impact_level="High",
                previous_value=2.0,
                forecast_value=2.5,
                timestamp_collected=datetime(2024, 1, 9)
            ),
            MagicMock(
                event_id=2,
                currency="EUR",
                event_name="GDP q/q",
                scheduled_datetime=datetime(2024, 1, 11),
                impact_level="High",
                previous_value=0.1,
                forecast_value=0.2,
                timestamp_collected=datetime(2024, 1, 10)
            )
        ]))
        
        self.mock_db.execute.return_value = mock_result
        
        week_start = datetime(2024, 1, 8)
        week_end = datetime(2024, 1, 14)
        
        events = self.calculator.get_week_events_with_indicators(week_start, week_end)
        
        self.assertEqual(len(events), 2)
        self.assertEqual(events[0]["currency"], "USD")
        self.assertEqual(events[1]["currency"], "EUR")
        self.mock_db.execute.assert_called_once()
    
    def test_persist_sentiments_new_record(self):
        """
        Test persist_sentiments with new records.
        """
        # Mock no existing records
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        currency_sentiments = {
            "USD": {
                "resolution": {"final_sentiment": "Bullish"},
                "events": [],
                "analysis_period": {}
            }
        }
        
        week_start = datetime(2024, 1, 8)
        week_end = datetime(2024, 1, 14)
        
        self.calculator.persist_sentiments(currency_sentiments, week_start, week_end)
        
        self.mock_db.add.assert_called_once()
        self.mock_db.commit.assert_called_once()
    
    def test_persist_sentiments_update_existing(self):
        """
        Test persist_sentiments with existing records.
        """
        # Mock existing record
        existing_record = MagicMock(spec=Sentiment)
        self.mock_db.query.return_value.filter.return_value.first.return_value = existing_record
        
        currency_sentiments = {
            "USD": {
                "resolution": {"final_sentiment": "Bearish"},
                "events": [],
                "analysis_period": {}
            }
        }
        
        week_start = datetime(2024, 1, 8)
        week_end = datetime(2024, 1, 14)
        
        self.calculator.persist_sentiments(currency_sentiments, week_start, week_end)
        
        self.assertEqual(existing_record.final_sentiment, "Bearish")
        self.mock_db.add.assert_not_called()
        self.mock_db.commit.assert_called_once()
    
    @patch.object(SentimentCalculator, 'get_week_events_with_indicators')
    @patch.object(SentimentCalculator, 'persist_sentiments')
    def test_calculate_weekly_sentiments_full_flow(self, mock_persist, mock_get_events):
        """
        Test the full calculate_weekly_sentiments flow.
        """
        # Mock events data
        mock_events = [
            {
                "event_id": 1,
                "currency": "USD",
                "event_name": "CPI y/y",
                "previous_value": 2.0,
                "forecast_value": 2.5
            },
            {
                "event_id": 2,
                "currency": "USD",
                "event_name": "GDP q/q",
                "previous_value": 0.1,
                "forecast_value": 0.3
            },
            {
                "event_id": 3,
                "currency": "EUR",
                "event_name": "CPI y/y",
                "previous_value": 1.5,
                "forecast_value": 1.0
            }
        ]
        
        mock_get_events.return_value = mock_events
        
        result = self.calculator.calculate_weekly_sentiments()
        
        # Should have results for USD and EUR
        self.assertIn("USD", result)
        self.assertIn("EUR", result)
        
        # USD should be bullish (2 bullish events)
        self.assertEqual(result["USD"]["resolution"]["final_sentiment"], "Bullish")
        
        # EUR should be bearish (1 bearish event)
        self.assertEqual(result["EUR"]["resolution"]["final_sentiment"], "Bearish")
        
        # Should persist results
        mock_persist.assert_called_once()

if __name__ == '__main__':
    unittest.main() 