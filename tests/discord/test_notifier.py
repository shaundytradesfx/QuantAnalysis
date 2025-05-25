"""
Unit tests for Discord notifier functionality.
"""
import pytest
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import requests

from src.discord.notifier import DiscordNotifier


class TestDiscordNotifier:
    """Test cases for DiscordNotifier class."""

    @pytest.fixture
    def mock_webhook_urls(self):
        """Mock webhook URLs for testing."""
        return {
            "webhook_url": "https://discord.com/api/webhooks/test/main",
            "health_webhook_url": "https://discord.com/api/webhooks/test/health"
        }

    @pytest.fixture
    def notifier(self, mock_webhook_urls):
        """Create DiscordNotifier instance for testing."""
        return DiscordNotifier(
            webhook_url=mock_webhook_urls["webhook_url"],
            health_webhook_url=mock_webhook_urls["health_webhook_url"]
        )

    @pytest.fixture
    def sample_sentiment_data(self):
        """Sample sentiment data for testing."""
        return {
            "USD": {
                "currency": "USD",
                "events": [
                    {
                        "event_name": "CPI y/y",
                        "previous": 2.1,
                        "forecast": 2.3,
                        "sentiment": 1,
                        "sentiment_label": "Bullish",
                        "data_available": True
                    },
                    {
                        "event_name": "Unemployment Rate",
                        "previous": 3.8,
                        "forecast": 3.7,
                        "sentiment": 1,
                        "sentiment_label": "Bullish",
                        "data_available": True
                    }
                ],
                "resolution": {
                    "final_sentiment": "Bullish",
                    "final_sentiment_value": 1,
                    "reason": "Majority bullish (2/2 events)",
                    "event_count": 2,
                    "sentiment_breakdown": {"bullish": 2, "bearish": 0, "neutral": 0}
                }
            },
            "EUR": {
                "currency": "EUR",
                "events": [
                    {
                        "event_name": "PMI Manufacturing",
                        "previous": 49.2,
                        "forecast": 48.8,
                        "sentiment": -1,
                        "sentiment_label": "Bearish",
                        "data_available": True
                    }
                ],
                "resolution": {
                    "final_sentiment": "Bearish",
                    "final_sentiment_value": -1,
                    "reason": "Majority bearish (1/1 events)",
                    "event_count": 1,
                    "sentiment_breakdown": {"bullish": 0, "bearish": 1, "neutral": 0}
                }
            }
        }

    def test_init_with_urls(self, mock_webhook_urls):
        """Test notifier initialization with explicit URLs."""
        notifier = DiscordNotifier(
            webhook_url=mock_webhook_urls["webhook_url"],
            health_webhook_url=mock_webhook_urls["health_webhook_url"]
        )
        
        assert notifier.webhook_url == mock_webhook_urls["webhook_url"]
        assert notifier.health_webhook_url == mock_webhook_urls["health_webhook_url"]
        assert notifier.currency_priority == ["USD", "EUR", "GBP", "JPY", "AUD", "NZD", "CAD", "CHF"]

    def test_init_with_env_vars(self):
        """Test notifier initialization with environment variables."""
        with patch.dict('os.environ', {
            'DISCORD_WEBHOOK_URL': 'https://discord.com/api/webhooks/env/main',
            'DISCORD_HEALTH_WEBHOOK_URL': 'https://discord.com/api/webhooks/env/health'
        }):
            notifier = DiscordNotifier()
            assert notifier.webhook_url == 'https://discord.com/api/webhooks/env/main'
            assert notifier.health_webhook_url == 'https://discord.com/api/webhooks/env/health'

    def test_init_no_webhooks(self):
        """Test notifier initialization with no webhook URLs."""
        with patch.dict('os.environ', {}, clear=True):
            notifier = DiscordNotifier()
            assert notifier.webhook_url is None
            assert notifier.health_webhook_url is None

    def test_get_flag_emoji(self, notifier):
        """Test flag emoji mapping."""
        assert notifier._get_flag_emoji("USD") == "🇺🇸"
        assert notifier._get_flag_emoji("EUR") == "🇪🇺"
        assert notifier._get_flag_emoji("GBP") == "🇬🇧"
        assert notifier._get_flag_emoji("JPY") == "🇯🇵"
        assert notifier._get_flag_emoji("UNKNOWN") == "🏳️"

    def test_get_sentiment_emoji(self, notifier):
        """Test sentiment emoji mapping."""
        assert notifier._get_sentiment_emoji("Bullish") == "🟢"
        assert notifier._get_sentiment_emoji("Bullish with Consolidation") == "🟢"
        assert notifier._get_sentiment_emoji("Bearish") == "🔴"
        assert notifier._get_sentiment_emoji("Bearish with Consolidation") == "🔴"
        assert notifier._get_sentiment_emoji("Neutral") == "⚪"

    def test_sort_currencies_by_priority(self, notifier):
        """Test currency sorting by priority."""
        currencies = ["CHF", "GBP", "AUD", "USD", "ZAR", "EUR"]
        sorted_currencies = notifier._sort_currencies_by_priority(currencies)
        
        # Should start with priority currencies in order
        expected_start = ["USD", "EUR", "GBP", "AUD", "CHF"]
        assert sorted_currencies[:5] == expected_start
        
        # Should end with remaining currencies alphabetically
        assert "ZAR" in sorted_currencies
        assert sorted_currencies.index("ZAR") == len(sorted_currencies) - 1

    def test_generate_narrative(self, notifier):
        """Test narrative generation for different sentiments."""
        # Test bullish narrative
        narrative = notifier._generate_narrative("USD", "Bullish", 2)
        assert "Positive economic indicators" in narrative
        assert "upside potential" in narrative
        assert "USD" in narrative
        
        # Test bearish narrative
        narrative = notifier._generate_narrative("EUR", "Bearish", 1)
        assert "Negative economic indicators" in narrative
        assert "downside pressure" in narrative
        assert "EUR" in narrative
        
        # Test neutral narrative
        narrative = notifier._generate_narrative("GBP", "Neutral", 1)
        assert "Neutral signals" in narrative
        assert "sideways movement" in narrative
        assert "GBP" in narrative
        
        # Test consolidation narratives
        narrative = notifier._generate_narrative("JPY", "Bullish with Consolidation", 3)
        assert "Mixed signals with bullish lean" in narrative
        assert "cautious optimism" in narrative
        
        narrative = notifier._generate_narrative("CAD", "Bearish with Consolidation", 3)
        assert "Mixed signals with bearish lean" in narrative
        assert "cautious pessimism" in narrative

    def test_get_next_monday(self, notifier):
        """Test next Monday calculation."""
        # Test with a Monday
        monday = datetime(2024, 7, 29)  # A Monday
        next_monday = notifier._get_next_monday(monday)
        expected = datetime(2024, 8, 5)  # Next Monday
        assert next_monday == expected
        
        # Test with a different day
        wednesday = datetime(2024, 7, 31)  # A Wednesday
        next_monday = notifier._get_next_monday(wednesday)
        expected = datetime(2024, 8, 7)  # Following Monday
        assert next_monday == expected

    def test_format_currency_section(self, notifier, sample_sentiment_data):
        """Test currency section formatting."""
        usd_data = sample_sentiment_data["USD"]
        section, summary = notifier._format_currency_section("USD", usd_data)
        
        # Check section contains expected elements
        assert "🇺🇸 USD" in section
        assert "CPI y/y" in section
        assert "Unemployment Rate" in section
        assert "Prev=2.10" in section
        assert "Forecast=2.30" in section
        assert "🟢 Bullish" in section
        assert "Overall" in section
        assert "Positive economic indicators" in section
        
        # Check summary
        assert summary == "USD: Bullish"

    def test_format_currency_section_missing_data(self, notifier):
        """Test currency section formatting with missing data."""
        missing_data = {
            "currency": "GBP",
            "events": [
                {
                    "event_name": "CPI y/y",
                    "data_available": False,
                    "sentiment_label": "Neutral"
                }
            ],
            "resolution": {
                "final_sentiment": "Neutral",
                "reason": "Data unavailable"
            }
        }
        
        section, summary = notifier._format_currency_section("GBP", missing_data)
        
        assert "🇬🇧 GBP" in section
        assert "Data Unavailable" in section
        assert "⚪ Neutral" in section
        assert summary == "GBP: Neutral"

    def test_format_empty_report(self, notifier):
        """Test empty report formatting."""
        week_start = datetime(2024, 7, 29)
        message = notifier._format_empty_report(week_start)
        
        assert "Economic Directional Analysis: Week of July 29, 2024" in message
        assert "No high-impact economic events found" in message
        assert "Light economic calendar" in message
        assert "Data collection issues" in message
        assert "EconSentimentBot" in message

    def test_format_weekly_report(self, notifier, sample_sentiment_data):
        """Test complete weekly report formatting."""
        week_start = datetime(2024, 7, 29)
        message = notifier.format_weekly_report(sample_sentiment_data, week_start)
        
        # Check header
        assert "📊 Economic Directional Analysis: Week of July 29, 2024" in message
        
        # Check currencies are present (USD should come before EUR due to priority)
        usd_index = message.find("🇺🇸 USD")
        eur_index = message.find("🇪🇺 EUR")
        assert usd_index < eur_index
        
        # Check net summary
        assert "📈 Net Summary:" in message
        assert "USD: Bullish" in message
        assert "EUR: Bearish" in message
        
        # Check footer
        assert "EconSentimentBot" in message
        assert "Next run: August 05, 2024" in message

    def test_format_weekly_report_empty(self, notifier):
        """Test weekly report formatting with empty data."""
        week_start = datetime(2024, 7, 29)
        message = notifier.format_weekly_report({}, week_start)
        
        assert "No high-impact economic events found" in message

    @patch('src.discord.notifier.requests.Session.post')
    def test_send_weekly_report_success(self, mock_post, notifier, sample_sentiment_data):
        """Test successful weekly report sending."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response
        
        week_start = datetime(2024, 7, 29)
        result = notifier.send_weekly_report(sample_sentiment_data, week_start)
        
        assert result is True
        mock_post.assert_called_once()
        
        # Check call arguments
        call_args = mock_post.call_args
        assert call_args[0][0] == notifier.webhook_url
        
        # Check payload
        payload = call_args[1]['json']
        assert payload['username'] == 'EconSentimentBot'
        assert 'Economic Directional Analysis' in payload['content']

    @patch('src.discord.notifier.requests.Session.post')
    def test_send_weekly_report_failure(self, mock_post, notifier, sample_sentiment_data):
        """Test weekly report sending failure."""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_post.return_value = mock_response
        
        week_start = datetime(2024, 7, 29)
        result = notifier.send_weekly_report(sample_sentiment_data, week_start)
        
        assert result is False
        # Should attempt to send both main message and health alert
        assert mock_post.call_count >= 1

    def test_send_weekly_report_no_webhook(self, sample_sentiment_data):
        """Test weekly report sending with no webhook URL."""
        notifier = DiscordNotifier()  # No webhook URL
        
        week_start = datetime(2024, 7, 29)
        result = notifier.send_weekly_report(sample_sentiment_data, week_start)
        
        assert result is False

    @patch('src.discord.notifier.requests.Session.post')
    def test_send_weekly_report_network_error(self, mock_post, notifier, sample_sentiment_data):
        """Test weekly report sending with network error."""
        # Mock network exception
        mock_post.side_effect = requests.exceptions.ConnectionError("Network error")
        
        week_start = datetime(2024, 7, 29)
        result = notifier.send_weekly_report(sample_sentiment_data, week_start)
        
        assert result is False

    @patch('src.discord.notifier.requests.Session.post')
    def test_send_health_alert_success(self, mock_post, notifier):
        """Test successful health alert sending."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response
        
        result = notifier.send_health_alert("Test Alert", "Test message", "ERROR")
        
        assert result is True
        mock_post.assert_called_once()
        
        # Check payload
        call_args = mock_post.call_args
        payload = call_args[1]['json']
        assert payload['username'] == 'EconSentimentBot Health'
        assert '🚨 **ERROR: Test Alert**' in payload['content']
        assert 'Test message' in payload['content']

    @patch('src.discord.notifier.requests.Session.post')
    def test_send_health_alert_different_severities(self, mock_post, notifier):
        """Test health alerts with different severity levels."""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response
        
        # Test ERROR
        notifier.send_health_alert("Error", "Error message", "ERROR")
        payload = mock_post.call_args[1]['json']
        assert '🚨 **ERROR:' in payload['content']
        
        # Test WARNING
        notifier.send_health_alert("Warning", "Warning message", "WARNING")
        payload = mock_post.call_args[1]['json']
        assert '⚠️ **WARNING:' in payload['content']
        
        # Test INFO
        notifier.send_health_alert("Info", "Info message", "INFO")
        payload = mock_post.call_args[1]['json']
        assert 'ℹ️ **INFO:' in payload['content']

    def test_send_health_alert_no_webhook(self):
        """Test health alert with no health webhook URL."""
        notifier = DiscordNotifier()  # No webhook URLs
        
        result = notifier.send_health_alert("Test", "Test message")
        
        assert result is False

    @patch('src.discord.notifier.requests.Session.post')
    def test_test_connection_both_webhooks(self, mock_post, notifier):
        """Test connection testing with both webhooks configured."""
        # Mock successful responses
        mock_response = Mock()
        mock_response.status_code = 204
        mock_post.return_value = mock_response
        
        results = notifier.test_connection()
        
        assert results["main_webhook"] is True
        assert results["health_webhook"] is True
        assert mock_post.call_count == 2

    @patch('src.discord.notifier.requests.Session.post')
    def test_test_connection_failures(self, mock_post, notifier):
        """Test connection testing with failures."""
        # Mock failed responses
        mock_response = Mock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response
        
        results = notifier.test_connection()
        
        assert results["main_webhook"] is False
        assert results["health_webhook"] is False

    def test_test_connection_no_webhooks(self):
        """Test connection testing with no webhooks configured."""
        notifier = DiscordNotifier()  # No webhook URLs
        
        results = notifier.test_connection()
        
        assert results["main_webhook"] is False
        assert results["health_webhook"] is False

    @patch('src.discord.notifier.requests.Session.post')
    def test_test_connection_network_error(self, mock_post, notifier):
        """Test connection testing with network errors."""
        # Mock network exception
        mock_post.side_effect = requests.exceptions.ConnectionError("Network error")
        
        results = notifier.test_connection()
        
        assert results["main_webhook"] is False
        # Health webhook test might not be reached due to exception 