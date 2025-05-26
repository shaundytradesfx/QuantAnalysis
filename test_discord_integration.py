#!/usr/bin/env python3
"""
Test script to verify Discord webhook integration with a real message.
"""
import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.discord.notifier import DiscordNotifier

def main():
    """Send a test message to Discord to verify integration."""
    print("🧪 Testing Discord Integration with Real Webhook...")
    
    # Create sample sentiment data
    sample_data = {
        "USD": {
            "currency": "USD",
            "events": [
                {
                    "event_name": "CPI y/y (Test)",
                    "previous": 2.1,
                    "forecast": 2.3,
                    "sentiment": 1,
                    "sentiment_label": "Bullish",
                    "data_available": True
                }
            ],
            "resolution": {
                "final_sentiment": "Bullish",
                "final_sentiment_value": 1,
                "reason": "Discord Integration Test",
                "event_count": 1,
                "sentiment_breakdown": {"bullish": 1, "bearish": 0, "neutral": 0}
            }
        }
    }
    
    # Initialize notifier
    notifier = DiscordNotifier()
    
    # Get current week start (Monday)
    week_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    while week_start.weekday() != 0:  # Monday is 0
        week_start -= timedelta(days=1)
    
    # Send test message
    print("📤 Sending test message to Discord...")
    success = notifier.send_weekly_report(sample_data, week_start)
    
    if success:
        print("✅ SUCCESS: Discord message sent successfully!")
        print("🎉 Discord webhook integration is working correctly!")
        return 0
    else:
        print("❌ FAILED: Could not send Discord message")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 