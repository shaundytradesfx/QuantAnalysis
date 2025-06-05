"""
Discord notification module for sending weekly sentiment reports.

This module handles:
- Message formatting with Markdown support
- Discord webhook integration
- Error handling and retry logic
- Health check notifications
- Phase 4: Actual sentiment reporting with accuracy metrics
"""
import os
import json
import time
import logging
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from functools import wraps
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ..utils.logging import get_logger

logger = get_logger(__name__)

def timing_decorator(func):
    """
    Simple timing decorator for Discord notifier methods.
    
    Args:
        func: The function to measure.
        
    Returns:
        function: The wrapped function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"Function {func.__name__} executed in {execution_time:.2f} seconds")
        return result
    return wrapper

class DiscordNotifier:
    """
    Handles Discord webhook notifications for sentiment analysis reports.
    Phase 4: Enhanced with actual sentiment data and accuracy tracking.
    """
    
    def __init__(self, webhook_url: str = None, health_webhook_url: str = None):
        """
        Initialize Discord notifier.
        
        Args:
            webhook_url (str, optional): Discord webhook URL for reports
            health_webhook_url (str, optional): Discord webhook URL for health alerts
        """
        self.webhook_url = webhook_url or os.getenv("DISCORD_WEBHOOK_URL")
        self.health_webhook_url = health_webhook_url or os.getenv("DISCORD_HEALTH_WEBHOOK_URL")
        
        # Phase 4: Configuration for actual sentiment reporting
        self.include_actual_sentiment = os.getenv("INCLUDE_ACTUAL_SENTIMENT_IN_REPORTS", "true").lower() == "true"
        self.show_forecast_accuracy = os.getenv("SHOW_FORECAST_ACCURACY_IN_REPORTS", "true").lower() == "true"
        self.show_surprises = os.getenv("SHOW_SURPRISES_IN_REPORTS", "true").lower() == "true"
        
        if not self.webhook_url:
            logger.warning("No Discord webhook URL configured")
        
        # Configure HTTP session with retries
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
            backoff_factor=1
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Currency priority order for display
        self.currency_priority = ["USD", "EUR", "GBP", "JPY", "AUD", "NZD", "CAD", "CHF"]
    
    def format_weekly_report(self, currency_sentiments: Dict[str, Any], week_start: datetime) -> str:
        """
        Format the weekly sentiment analysis into a Discord-friendly message.
        Phase 4: Enhanced with actual sentiment data and accuracy metrics.
        
        Args:
            currency_sentiments (Dict[str, Any]): Sentiment analysis results by currency
            week_start (datetime): Start date of the analysis week
            
        Returns:
            str: Formatted Discord message with Markdown
        """
        if not currency_sentiments:
            return self._format_empty_report(week_start)
        
        # Build message sections
        header = f"**📊 Economic Directional Analysis: Week of {week_start.strftime('%B %d, %Y')}**\n\n"
        
        # Sort currencies by priority
        sorted_currencies = self._sort_currencies_by_priority(list(currency_sentiments.keys()))
        
        # Currency sections
        currency_sections = []
        net_summary = []
        accuracy_data = []
        surprises = []
        
        for currency in sorted_currencies:
            sentiment_data = currency_sentiments[currency]
            section, summary, accuracy, currency_surprises = self._format_currency_section(currency, sentiment_data)
            currency_sections.append(section)
            net_summary.append(summary)
            if accuracy is not None:
                accuracy_data.append((currency, accuracy))
            surprises.extend(currency_surprises)
        
        # Build complete message
        message_parts = [header]
        message_parts.extend(currency_sections)
        
        # Add net summary
        message_parts.append("\n**📈 Summary:** " + " | ".join(net_summary))
        
        # Phase 4: Add accuracy section if enabled and data available
        if self.show_forecast_accuracy and accuracy_data:
            accuracy_section = self._format_accuracy_section(accuracy_data)
            message_parts.append(accuracy_section)
        
        # Phase 4: Add surprises section if enabled and surprises found
        if self.show_surprises and surprises:
            surprises_section = self._format_surprises_section(surprises)
            message_parts.append(surprises_section)
        
        # Footer
        message_parts.append(f"\n_Next run: {self._get_next_monday(week_start).strftime('%b %d')} 06:00 UTC_")
        
        return "\n".join(message_parts)
    
    def _format_currency_section(self, currency: str, sentiment_data: Dict[str, Any]) -> Tuple[str, str, Optional[float], List[Dict]]:
        """
        Format a single currency's sentiment section.
        Phase 4: Enhanced with actual sentiment data and accuracy tracking.
        
        Args:
            currency (str): Currency code
            sentiment_data (Dict[str, Any]): Sentiment analysis data
            
        Returns:
            tuple: (formatted_section, summary_line, accuracy_percentage, surprises_list)
        """
        events = sentiment_data.get("events", [])
        final_sentiment = sentiment_data.get("final_sentiment", "Neutral")
        
        # Phase 4: Get actual sentiment data if available
        actual_sentiment = sentiment_data.get("actual_sentiment", final_sentiment)
        forecast_accuracy = sentiment_data.get("forecast_accuracy")
        actual_available = sentiment_data.get("actual_available", False)
        
        # Currency header with flag emoji
        flag_emoji = self._get_flag_emoji(currency)
        sentiment_emoji = self._get_sentiment_emoji(final_sentiment)
        
        # Phase 4: Actual sentiment emoji if different from forecast
        actual_emoji = ""
        accuracy_indicator = ""
        if self.include_actual_sentiment and actual_available:
            actual_emoji = self._get_sentiment_emoji(actual_sentiment)
            if actual_sentiment == final_sentiment:
                accuracy_indicator = " ✅"
            else:
                accuracy_indicator = " ❌"
        
        # Count events by sentiment
        bullish_count = sum(1 for e in events if e.get("sentiment", 0) > 0)
        bearish_count = sum(1 for e in events if e.get("sentiment", 0) < 0)
        neutral_count = sum(1 for e in events if e.get("sentiment", 0) == 0)
        
        # Create concise event summary
        event_summary = []
        if bullish_count > 0:
            event_summary.append(f"🟢{bullish_count}")
        if bearish_count > 0:
            event_summary.append(f"🔴{bearish_count}")
        if neutral_count > 0:
            event_summary.append(f"⚪{neutral_count}")
        
        events_text = " | ".join(event_summary) if event_summary else "No events"
        
        # Phase 4: Enhanced key events with actual data
        key_events = []
        surprises = []
        data_events = [e for e in events if e.get("data_available", True) and e.get("sentiment", 0) != 0]
        
        # Sort by absolute sentiment value and take top 2
        data_events.sort(key=lambda x: abs(x.get("sentiment", 0)), reverse=True)
        for event in data_events[:2]:
            event_name = event.get("event_name", "Unknown")
            # Shorten common event names
            event_name = event_name.replace("Preliminary", "Prelim").replace("Manufacturing", "Mfg")
            if len(event_name) > 20:
                event_name = event_name[:17] + "..."
            
            # Phase 4: Add actual data if available
            if self.include_actual_sentiment and event.get("actual_available"):
                forecast_val = event.get("forecast_value")
                actual_val = event.get("actual_value")
                if forecast_val is not None and actual_val is not None:
                    key_events.append(f"{event_name} (F:{forecast_val:.1f}, A:{actual_val:.1f})")
                else:
                    key_events.append(event_name)
                
                # Check for surprises
                event_accuracy = event.get("accuracy", "")
                if event_accuracy == "mismatch":
                    surprises.append({
                        "currency": currency,
                        "event": event_name,
                        "forecast_sentiment": event.get("sentiment_label", "Unknown"),
                        "actual_sentiment": event.get("actual_sentiment_label", "Unknown"),
                        "forecast_value": forecast_val,
                        "actual_value": actual_val
                    })
            else:
            key_events.append(event_name)
        
        key_events_text = ", ".join(key_events) if key_events else "No key events"
        
        # Phase 4: Format section with actual sentiment if available
        if self.include_actual_sentiment and actual_available:
            if actual_sentiment != final_sentiment:
                section = f"**{flag_emoji} {currency}**: {sentiment_emoji} {final_sentiment} → {actual_emoji} **{actual_sentiment}**{accuracy_indicator} ({events_text})\n   Key: {key_events_text}"
            else:
                section = f"**{flag_emoji} {currency}**: {sentiment_emoji} **{final_sentiment}**{accuracy_indicator} ({events_text})\n   Key: {key_events_text}"
        else:
        section = f"**{flag_emoji} {currency}**: {sentiment_emoji} {final_sentiment} ({events_text})\n   Key: {key_events_text}"
        
        # Summary for net section
        if self.include_actual_sentiment and actual_available:
            summary = f"{currency}: {actual_sentiment}"
        else:
        summary = f"{currency}: {final_sentiment}"
        
        return section, summary, forecast_accuracy, surprises
    
    def _format_accuracy_section(self, accuracy_data: List[Tuple[str, float]]) -> str:
        """
        Format forecast accuracy section.
        Phase 4: New method for accuracy reporting.
        
        Args:
            accuracy_data: List of (currency, accuracy_percentage) tuples
            
        Returns:
            str: Formatted accuracy section
        """
        if not accuracy_data:
            return ""
        
        # Calculate overall accuracy
        valid_accuracies = [acc for _, acc in accuracy_data if acc is not None]
        if valid_accuracies:
            overall_accuracy = sum(valid_accuracies) / len(valid_accuracies)
            overall_emoji = "🎯" if overall_accuracy >= 80 else "📊" if overall_accuracy >= 60 else "⚠️"
        else:
            overall_accuracy = 0
            overall_emoji = "❓"
        
        accuracy_lines = [f"\n**{overall_emoji} Forecast Accuracy: {overall_accuracy:.0f}%**"]
        
        # Individual currency accuracies
        currency_accuracies = []
        for currency, accuracy in accuracy_data:
            if accuracy is not None:
                acc_emoji = "✅" if accuracy >= 80 else "🟡" if accuracy >= 60 else "🔴"
                currency_accuracies.append(f"{acc_emoji} {currency}: {accuracy:.0f}%")
        
        if currency_accuracies:
            accuracy_lines.append(" | ".join(currency_accuracies))
        
        return "\n".join(accuracy_lines)
    
    def _format_surprises_section(self, surprises: List[Dict]) -> str:
        """
        Format surprises section for major forecast mismatches.
        Phase 4: New method for highlighting prediction surprises.
        
        Args:
            surprises: List of surprise event dictionaries
            
        Returns:
            str: Formatted surprises section
        """
        if not surprises:
            return ""
        
        surprise_lines = ["\n**🚨 Market Surprises:**"]
        
        for surprise in surprises[:3]:  # Limit to top 3 surprises
            currency = surprise["currency"]
            event = surprise["event"]
            forecast_sent = surprise["forecast_sentiment"]
            actual_sent = surprise["actual_sentiment"]
            forecast_val = surprise.get("forecast_value")
            actual_val = surprise.get("actual_value")
            
            if forecast_val is not None and actual_val is not None:
                surprise_lines.append(
                    f"• **{currency} {event}**: Expected {forecast_sent} (F:{forecast_val:.1f}) "
                    f"but got **{actual_sent}** (A:{actual_val:.1f})"
                )
            else:
                surprise_lines.append(
                    f"• **{currency} {event}**: Expected {forecast_sent} but got **{actual_sent}**"
                )
        
        return "\n".join(surprise_lines)
    
    def _format_empty_report(self, week_start: datetime) -> str:
        """Format message when no sentiment data is available."""
        return f"""**📊 Economic Directional Analysis: Week of {week_start.strftime('%B %d, %Y')}**

⚠️ **No high-impact economic events found for this week.**

This could indicate:
• Light economic calendar
• Data collection issues
• System maintenance

_Generated automatically by EconSentimentBot. Next run: {self._get_next_monday(week_start).strftime('%B %d, %Y')} at 06:00 UTC_"""
    
    def _sort_currencies_by_priority(self, currencies: list) -> list:
        """Sort currencies by predefined priority order."""
        sorted_currencies = []
        
        # Add currencies in priority order
        for priority_currency in self.currency_priority:
            if priority_currency in currencies:
                sorted_currencies.append(priority_currency)
        
        # Add any remaining currencies alphabetically
        remaining = sorted([c for c in currencies if c not in sorted_currencies])
        sorted_currencies.extend(remaining)
        
        return sorted_currencies
    
    def _get_flag_emoji(self, currency: str) -> str:
        """Get flag emoji for currency."""
        flag_map = {
            "USD": "🇺🇸", "EUR": "🇪🇺", "GBP": "🇬🇧", "JPY": "🇯🇵",
            "AUD": "🇦🇺", "NZD": "🇳🇿", "CAD": "🇨🇦", "CHF": "🇨🇭"
        }
        return flag_map.get(currency, "🏳️")
    
    def _get_sentiment_emoji(self, sentiment: str) -> str:
        """Get emoji for sentiment."""
        if "Bullish" in sentiment:
            return "🟢"
        elif "Bearish" in sentiment:
            return "🔴"
        else:
            return "⚪"
    
    def _generate_narrative(self, currency: str, sentiment: str, event_count: int) -> str:
        """Generate narrative description for currency sentiment."""
        if "Bullish" in sentiment:
            if "Consolidation" in sentiment:
                return f"Mixed signals with bullish lean suggest cautious optimism for {currency}-related assets"
            else:
                return f"Positive economic indicators suggest upside potential for {currency} & related assets"
        elif "Bearish" in sentiment:
            if "Consolidation" in sentiment:
                return f"Mixed signals with bearish lean suggest cautious pessimism for {currency}-related assets"
            else:
                return f"Negative economic indicators suggest downside pressure for {currency} & related assets"
        else:
            return f"Neutral signals suggest sideways movement for {currency} in the near term"
    
    def _get_next_monday(self, current_week_start: datetime) -> datetime:
        """Get the next Monday date."""
        from datetime import timedelta
        return current_week_start + timedelta(days=7)
    
    @timing_decorator
    def send_weekly_report(self, currency_sentiments: Dict[str, Any], week_start: datetime) -> bool:
        """
        Send weekly sentiment report to Discord.
        
        Args:
            currency_sentiments (Dict[str, Any]): Sentiment analysis results
            week_start (datetime): Start date of analysis week
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        if not self.webhook_url:
            logger.error("No Discord webhook URL configured for weekly reports")
            return False
        
        try:
            # Format message
            message = self.format_weekly_report(currency_sentiments, week_start)
            
            # Prepare Discord payload
            payload = {
                "content": message,
                "username": "EconSentimentBot",
                "avatar_url": "https://images.emojiterra.com/twitter/v14.0/512px/1f4ca.png"
            }
            
            # Send to Discord
            logger.info(f"Sending weekly report to Discord for week of {week_start.strftime('%Y-%m-%d')}")
            response = self.session.post(
                self.webhook_url,
                json=payload,
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 204:
                logger.info("Weekly report sent successfully to Discord")
                return True
            else:
                logger.error(f"Failed to send Discord message: {response.status_code} - {response.text}")
                
                # Try sending health alert
                self._send_health_alert(
                    "Weekly Report Send Failed",
                    f"HTTP {response.status_code}: {response.text[:500]}"
                )
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error sending Discord message: {str(e)}")
            self._send_health_alert("Weekly Report Network Error", str(e))
            return False
        except Exception as e:
            logger.error(f"Unexpected error sending Discord message: {str(e)}")
            self._send_health_alert("Weekly Report Unexpected Error", str(e))
            return False
    
    def send_health_alert(self, title: str, message: str, severity: str = "ERROR") -> bool:
        """
        Send health check alert to Discord.
        
        Args:
            title (str): Alert title
            message (str): Alert message
            severity (str): Severity level (ERROR, WARNING, INFO)
            
        Returns:
            bool: True if sent successfully, False otherwise
        """
        return self._send_health_alert(title, message, severity)
    
    def _send_health_alert(self, title: str, message: str, severity: str = "ERROR") -> bool:
        """Internal method to send health alerts."""
        if not self.health_webhook_url:
            logger.warning("No health webhook URL configured for alerts")
            return False
        
        try:
            # Severity emoji
            severity_emoji = {
                "ERROR": "🚨",
                "WARNING": "⚠️",
                "INFO": "ℹ️"
            }.get(severity, "❓")
            
            # Format alert message
            alert_message = f"""{severity_emoji} **{severity}: {title}**

**Details:**
```
{message[:1500]}
```

**Timestamp:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
**Source:** EconSentimentBot Health Monitor"""
            
            payload = {
                "content": alert_message,
                "username": "EconSentimentBot Health",
                "avatar_url": "https://images.emojiterra.com/twitter/v14.0/512px/1f6a8.png"
            }
            
            response = self.session.post(
                self.health_webhook_url,
                json=payload,
                timeout=30,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 204:
                logger.info(f"Health alert sent successfully: {title}")
                return True
            else:
                logger.error(f"Failed to send health alert: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to send health alert: {str(e)}")
            return False
    
    def test_connection(self) -> Dict[str, bool]:
        """
        Test Discord webhook connections.
        
        Returns:
            Dict[str, bool]: Test results for each webhook
        """
        results = {}
        
        # Test main webhook
        if self.webhook_url:
            test_message = f"🧪 **Connection Test**\n\nEconSentimentBot connection test successful!\n\n_Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC_"
            payload = {
                "content": test_message,
                "username": "EconSentimentBot Test",
                "avatar_url": "https://images.emojiterra.com/twitter/v14.0/512px/1f9ea.png"
            }
            
            try:
                response = self.session.post(self.webhook_url, json=payload, timeout=15)
                results["main_webhook"] = response.status_code == 204
                logger.info(f"Main webhook test: {'PASSED' if results['main_webhook'] else 'FAILED'}")
            except Exception as e:
                results["main_webhook"] = False
                logger.error(f"Main webhook test failed: {str(e)}")
        else:
            results["main_webhook"] = False
            logger.warning("Main webhook URL not configured")
        
        # Test health webhook
        if self.health_webhook_url:
            results["health_webhook"] = self._send_health_alert(
                "Connection Test",
                "Health webhook connection test successful!",
                "INFO"
            )
        else:
            results["health_webhook"] = False
            logger.warning("Health webhook URL not configured")
        
        return results 