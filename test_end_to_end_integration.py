"""
End-to-end integration test for the complete sentiment analysis and Discord notification flow.

This test verifies:
1. Database connectivity and schema
2. Sentiment calculation engine
3. Discord notification formatting and sending
4. Complete workflow integration
"""
import os
import sys
import pytest
import tempfile
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.database.config import Base
from src.database.models import Event, Indicator, Sentiment
from src.analysis.sentiment_engine import SentimentCalculator
from src.discord.notifier import DiscordNotifier


class TestEndToEndIntegration:
    """End-to-end integration tests."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary in-memory database for testing."""
        # Create temporary database
        engine = create_engine("sqlite:///:memory:", echo=False)
        Base.metadata.create_all(engine)
        
        # Create session
        Session = sessionmaker(bind=engine)
        session = Session()
        
        yield session
        
        session.close()

    @pytest.fixture
    def sample_events_data(self, temp_db):
        """Create sample events and indicators data."""
        # Create events for current week
        current_monday = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        while current_monday.weekday() != 0:  # Monday is 0
            current_monday -= timedelta(days=1)
        
        events_data = [
            {
                "currency": "USD",
                "event_name": "CPI y/y",
                "scheduled_datetime": current_monday + timedelta(days=1, hours=14, minutes=30),
                "impact_level": "High",
                "previous_value": 2.1,
                "forecast_value": 2.3
            },
            {
                "currency": "USD", 
                "event_name": "Unemployment Rate",
                "scheduled_datetime": current_monday + timedelta(days=2, hours=14, minutes=30),
                "impact_level": "High",
                "previous_value": 3.8,
                "forecast_value": 3.7
            },
            {
                "currency": "EUR",
                "event_name": "PMI Manufacturing",
                "scheduled_datetime": current_monday + timedelta(days=3, hours=10, minutes=0),
                "impact_level": "High",
                "previous_value": 49.2,
                "forecast_value": 48.8
            },
            {
                "currency": "GBP",
                "event_name": "GDP q/q",
                "scheduled_datetime": current_monday + timedelta(days=4, hours=9, minutes=30),
                "impact_level": "High",
                "previous_value": 0.2,
                "forecast_value": 0.2
            }
        ]
        
        # Insert events and indicators
        for event_data in events_data:
            # Create event
            event = Event(
                currency=event_data["currency"],
                event_name=event_data["event_name"],
                scheduled_datetime=event_data["scheduled_datetime"],
                impact_level=event_data["impact_level"]
            )
            temp_db.add(event)
            temp_db.flush()  # Get the ID
            
            # Create indicator
            indicator = Indicator(
                event_id=event.id,
                previous_value=event_data["previous_value"],
                forecast_value=event_data["forecast_value"]
            )
            temp_db.add(indicator)
        
        temp_db.commit()
        return events_data

    def test_database_setup_and_models(self, temp_db):
        """Test that database models work correctly."""
        # Test event creation
        event = Event(
            currency="USD",
            event_name="Test Event",
            scheduled_datetime=datetime.now(),
            impact_level="High"
        )
        temp_db.add(event)
        temp_db.flush()
        
        # Test indicator creation
        indicator = Indicator(
            event_id=event.id,
            previous_value=1.5,
            forecast_value=1.7
        )
        temp_db.add(indicator)
        temp_db.commit()
        
        # Verify data
        retrieved_event = temp_db.query(Event).filter_by(currency="USD").first()
        assert retrieved_event is not None
        assert retrieved_event.event_name == "Test Event"
        assert len(retrieved_event.indicators) == 1
        assert retrieved_event.indicators[0].previous_value == 1.5

    def test_sentiment_calculation_engine(self, temp_db, sample_events_data):
        """Test the complete sentiment calculation engine."""
        # Initialize calculator with test database
        calculator = SentimentCalculator(db_session=temp_db, threshold=0.0)
        
        # Calculate sentiments for current week
        sentiments = calculator.calculate_weekly_sentiments()
        
        # Verify results
        assert len(sentiments) == 3  # USD, EUR, GBP
        
        # Check USD sentiment (should be bullish: 2 bullish events)
        usd_sentiment = sentiments["USD"]
        assert usd_sentiment["currency"] == "USD"
        assert len(usd_sentiment["events"]) == 2
        assert usd_sentiment["resolution"]["final_sentiment"] == "Bullish"
        
        # Check EUR sentiment (should be bearish: 1 bearish event)
        eur_sentiment = sentiments["EUR"]
        assert eur_sentiment["currency"] == "EUR"
        assert len(eur_sentiment["events"]) == 1
        assert eur_sentiment["resolution"]["final_sentiment"] == "Bearish"
        
        # Check GBP sentiment (should be neutral: forecast == previous)
        gbp_sentiment = sentiments["GBP"]
        assert gbp_sentiment["currency"] == "GBP"
        assert len(gbp_sentiment["events"]) == 1
        assert gbp_sentiment["resolution"]["final_sentiment"] == "Neutral"

    def test_sentiment_persistence(self, temp_db, sample_events_data):
        """Test that sentiments are properly persisted to database."""
        # Calculate and persist sentiments
        calculator = SentimentCalculator(db_session=temp_db, threshold=0.0)
        sentiments = calculator.calculate_weekly_sentiments()
        
        # Verify sentiments were persisted
        persisted_sentiments = temp_db.query(Sentiment).all()
        assert len(persisted_sentiments) == 3
        
        # Check specific sentiment record
        usd_sentiment = temp_db.query(Sentiment).filter_by(currency="USD").first()
        assert usd_sentiment is not None
        assert usd_sentiment.final_sentiment == "Bullish"
        assert usd_sentiment.details_json is not None
        
        # Verify JSON details structure
        details = usd_sentiment.details_json
        assert "currency" in details
        assert "events" in details
        assert "resolution" in details
        assert len(details["events"]) == 2

    @patch('src.discord.notifier.requests.Session.post')
    def test_discord_notification_formatting(self, mock_post, temp_db, sample_events_data):
        """Test Discord notification message formatting."""
        # Mock successful Discord response
        mock_response = Mock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response
        
        # Calculate sentiments
        calculator = SentimentCalculator(db_session=temp_db, threshold=0.0)
        sentiments = calculator.calculate_weekly_sentiments()
        
        # Initialize Discord notifier
        notifier = DiscordNotifier(
            webhook_url="https://discord.com/api/webhooks/test/main",
            health_webhook_url="https://discord.com/api/webhooks/test/health"
        )
        
        # Send notification
        week_start, _ = calculator.get_current_week_bounds()
        success = notifier.send_weekly_report(sentiments, week_start)
        
        # Verify success
        assert success is True
        mock_post.assert_called_once()
        
        # Check message content
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        message_content = payload['content']
        
        # Verify message structure
        assert "📊 Economic Directional Analysis" in message_content
        assert "🇺🇸 USD" in message_content
        assert "🇪🇺 EUR" in message_content
        assert "🇬🇧 GBP" in message_content
        assert "📈 Net Summary:" in message_content
        assert "USD: Bullish" in message_content
        assert "EUR: Bearish" in message_content
        assert "GBP: Neutral" in message_content
        assert "EconSentimentBot" in message_content

    @patch('src.discord.notifier.requests.Session.post')
    def test_complete_end_to_end_workflow(self, mock_post, temp_db, sample_events_data):
        """Test the complete end-to-end workflow."""
        # Mock Discord responses
        mock_response = Mock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response
        
        # Step 1: Calculate sentiments
        calculator = SentimentCalculator(db_session=temp_db, threshold=0.0)
        sentiments = calculator.calculate_weekly_sentiments()
        
        # Step 2: Verify sentiments calculated correctly
        assert len(sentiments) == 3
        assert sentiments["USD"]["resolution"]["final_sentiment"] == "Bullish"
        assert sentiments["EUR"]["resolution"]["final_sentiment"] == "Bearish"
        assert sentiments["GBP"]["resolution"]["final_sentiment"] == "Neutral"
        
        # Step 3: Verify persistence
        persisted_count = temp_db.query(Sentiment).count()
        assert persisted_count == 3
        
        # Step 4: Send Discord notification
        notifier = DiscordNotifier(
            webhook_url="https://discord.com/api/webhooks/test/main"
        )
        week_start, _ = calculator.get_current_week_bounds()
        notification_success = notifier.send_weekly_report(sentiments, week_start)
        
        # Step 5: Verify notification sent
        assert notification_success is True
        mock_post.assert_called_once()
        
        # Step 6: Verify message quality
        payload = mock_post.call_args[1]['json']
        message = payload['content']
        
        # Check all currencies are mentioned with correct sentiments
        assert "USD: Bullish" in message
        assert "EUR: Bearish" in message
        assert "GBP: Neutral" in message
        
        # Check event details are included
        assert "CPI y/y" in message
        assert "Unemployment Rate" in message
        assert "PMI Manufacturing" in message
        assert "GDP q/q" in message

    def test_error_handling_no_data(self, temp_db):
        """Test error handling when no data is available."""
        # Test with empty database
        calculator = SentimentCalculator(db_session=temp_db, threshold=0.0)
        sentiments = calculator.calculate_weekly_sentiments()
        
        # Should return empty dict
        assert sentiments == {}
        
        # Test Discord notification with empty data
        notifier = DiscordNotifier(
            webhook_url="https://discord.com/api/webhooks/test/main"
        )
        
        with patch('src.discord.notifier.requests.Session.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 204
            mock_post.return_value = mock_response
            
            week_start, _ = calculator.get_current_week_bounds()
            success = notifier.send_weekly_report({}, week_start)
            
            assert success is True
            payload = mock_post.call_args[1]['json']
            message = payload['content']
            assert "No high-impact economic events found" in message

    @patch('src.discord.notifier.requests.Session.post')
    def test_discord_error_handling(self, mock_post, temp_db, sample_events_data):
        """Test Discord error handling."""
        # Mock Discord failure
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response
        
        # Calculate sentiments
        calculator = SentimentCalculator(db_session=temp_db, threshold=0.0)
        sentiments = calculator.calculate_weekly_sentiments()
        
        # Try to send notification
        notifier = DiscordNotifier(
            webhook_url="https://discord.com/api/webhooks/test/main",
            health_webhook_url="https://discord.com/api/webhooks/test/health"
        )
        
        week_start, _ = calculator.get_current_week_bounds()
        success = notifier.send_weekly_report(sentiments, week_start)
        
        # Should fail gracefully
        assert success is False
        # Should attempt to send health alert (multiple calls)
        assert mock_post.call_count >= 1

    def test_threshold_sensitivity(self, temp_db):
        """Test sentiment calculation with different thresholds."""
        # Create events with small differences
        event = Event(
            currency="USD",
            event_name="Test Event",
            scheduled_datetime=datetime.now(),
            impact_level="High"
        )
        temp_db.add(event)
        temp_db.flush()
        
        indicator = Indicator(
            event_id=event.id,
            previous_value=2.0,
            forecast_value=2.05  # Small difference
        )
        temp_db.add(indicator)
        temp_db.commit()
        
        # Test with threshold = 0.0 (should be bullish)
        calculator = SentimentCalculator(db_session=temp_db, threshold=0.0)
        sentiments = calculator.calculate_weekly_sentiments()
        assert sentiments["USD"]["resolution"]["final_sentiment"] == "Bullish"
        
        # Test with threshold = 0.1 (should be neutral)
        calculator = SentimentCalculator(db_session=temp_db, threshold=0.1)
        sentiments = calculator.calculate_weekly_sentiments()
        assert sentiments["USD"]["resolution"]["final_sentiment"] == "Neutral"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"]) 