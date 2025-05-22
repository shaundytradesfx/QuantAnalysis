"""
Tests for the ScraperDBManager class.
"""
import unittest
from unittest.mock import patch, MagicMock
import datetime

from src.scraper.db_manager import ScraperDBManager
from src.database.models import Event, Indicator

class TestScraperDBManager(unittest.TestCase):
    """
    Tests for the ScraperDBManager class.
    """
    
    def setUp(self):
        """
        Set up test resources.
        """
        self.mock_session = MagicMock()
        self.db_manager = ScraperDBManager(self.mock_session)
    
    def test_get_or_create_event_existing(self):
        """
        Test get_or_create_event with existing event.
        """
        # Setup mock
        mock_event = MagicMock(spec=Event)
        mock_query = self.mock_session.query.return_value.filter.return_value
        mock_query.first.return_value = mock_event
        
        # Test data
        event_data = {
            "currency": "USD",
            "event_name": "CPI y/y",
            "scheduled_datetime": datetime.datetime.now(),
            "impact_level": "High"
        }
        
        # Call method
        result = self.db_manager.get_or_create_event(event_data)
        
        # Assertions
        self.mock_session.query.assert_called_once_with(Event)
        self.assertEqual(result, mock_event)
        self.mock_session.add.assert_not_called()
    
    def test_get_or_create_event_new(self):
        """
        Test get_or_create_event with new event.
        """
        # Setup mock
        mock_query = self.mock_session.query.return_value.filter.return_value
        mock_query.first.return_value = None
        
        # Test data
        event_data = {
            "currency": "USD",
            "event_name": "CPI y/y",
            "scheduled_datetime": datetime.datetime.now(),
            "impact_level": "High"
        }
        
        # Call method
        result = self.db_manager.get_or_create_event(event_data)
        
        # Assertions
        self.mock_session.add.assert_called_once()
        self.mock_session.commit.assert_called_once()
        self.mock_session.refresh.assert_called_once()
        self.assertIsInstance(result, Event)
        self.assertEqual(result.currency, event_data["currency"])
        self.assertEqual(result.event_name, event_data["event_name"])
        self.assertEqual(result.scheduled_datetime, event_data["scheduled_datetime"])
        self.assertEqual(result.impact_level, event_data["impact_level"])
    
    def test_add_or_update_indicator_unchanged(self):
        """
        Test add_or_update_indicator with unchanged values.
        """
        # Setup mock
        mock_event = MagicMock(spec=Event, id=1)
        mock_indicator = MagicMock(spec=Indicator)
        mock_indicator.previous_value = 2.5
        mock_indicator.forecast_value = 3.0
        mock_query = self.mock_session.query.return_value.filter.return_value
        mock_query.order_by.return_value.first.return_value = mock_indicator
        
        # Call method
        result = self.db_manager.add_or_update_indicator(mock_event, 2.5, 3.0)
        
        # Assertions
        self.mock_session.query.assert_called_once_with(Indicator)
        self.assertEqual(result, mock_indicator)
        self.mock_session.add.assert_not_called()
    
    def test_add_or_update_indicator_changed(self):
        """
        Test add_or_update_indicator with changed values.
        """
        # Setup mock
        mock_event = MagicMock(spec=Event, id=1)
        mock_indicator = MagicMock(spec=Indicator)
        mock_indicator.previous_value = 2.5
        mock_indicator.forecast_value = 3.0
        mock_query = self.mock_session.query.return_value.filter.return_value
        mock_query.order_by.return_value.first.return_value = mock_indicator
        
        # Call method
        result = self.db_manager.add_or_update_indicator(mock_event, 2.5, 3.5)  # Changed forecast
        
        # Assertions
        self.mock_session.add.assert_called_once()
        self.mock_session.commit.assert_called_once()
        self.mock_session.refresh.assert_called_once()
        self.assertIsInstance(result, Indicator)
        self.assertEqual(result.event_id, mock_event.id)
        self.assertEqual(result.previous_value, 2.5)
        self.assertEqual(result.forecast_value, 3.5)
    
    def test_process_events(self):
        """
        Test process_events.
        """
        # Setup mocks
        mock_event = MagicMock(spec=Event)
        mock_indicator = MagicMock(spec=Indicator)
        
        # Patch methods
        with patch.object(self.db_manager, 'get_or_create_event', return_value=mock_event) as mock_get_event:
            with patch.object(self.db_manager, 'add_or_update_indicator', return_value=mock_indicator) as mock_add_indicator:
                
                # Test data
                events_data = [
                    {
                        "currency": "USD",
                        "event_name": "CPI y/y",
                        "scheduled_datetime": datetime.datetime.now(),
                        "impact_level": "High",
                        "previous_value": 2.5,
                        "forecast_value": 3.0
                    },
                    {
                        "currency": "EUR",
                        "event_name": "PMI",
                        "scheduled_datetime": datetime.datetime.now(),
                        "impact_level": "High",
                        "previous_value": 51.2,
                        "forecast_value": 52.0
                    }
                ]
                
                # Call method
                result = self.db_manager.process_events(events_data)
                
                # Assertions
                self.assertEqual(result, 2)
                self.assertEqual(mock_get_event.call_count, 2)
                self.assertEqual(mock_add_indicator.call_count, 2)

if __name__ == '__main__':
    unittest.main() 