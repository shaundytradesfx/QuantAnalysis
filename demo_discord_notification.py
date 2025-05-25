#!/usr/bin/env python3
"""
Demo script to test Discord notification functionality.

This script demonstrates the Discord notifier without requiring database setup.
"""
import sys
import os
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.discord.notifier import DiscordNotifier

def create_sample_sentiment_data():
    """Create sample sentiment data for testing."""
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
        },
        "GBP": {
            "currency": "GBP",
            "events": [
                {
                    "event_name": "GDP q/q",
                    "previous": 0.2,
                    "forecast": 0.2,
                    "sentiment": 0,
                    "sentiment_label": "Neutral",
                    "data_available": True
                }
            ],
            "resolution": {
                "final_sentiment": "Neutral",
                "final_sentiment_value": 0,
                "reason": "Majority neutral (1/1 events)",
                "event_count": 1,
                "sentiment_breakdown": {"bullish": 0, "bearish": 0, "neutral": 1}
            }
        }
    }

def test_message_formatting():
    """Test Discord message formatting."""
    print("🧪 Testing Discord message formatting...")
    
    # Create notifier (no webhook URLs needed for formatting test)
    notifier = DiscordNotifier()
    
    # Create sample data
    sentiment_data = create_sample_sentiment_data()
    week_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    while week_start.weekday() != 0:  # Monday is 0
        week_start -= timedelta(days=1)
    
    # Format message
    message = notifier.format_weekly_report(sentiment_data, week_start)
    
    print("📊 Generated Discord Message:")
    print("=" * 80)
    print(message)
    print("=" * 80)
    
    # Verify message contains expected elements
    checks = [
        ("Header", "📊 Economic Directional Analysis" in message),
        ("USD Currency", "🇺🇸 USD" in message),
        ("EUR Currency", "🇪🇺 EUR" in message),
        ("GBP Currency", "🇬🇧 GBP" in message),
        ("Net Summary", "📈 Net Summary:" in message),
        ("USD Bullish", "USD: Bullish" in message),
        ("EUR Bearish", "EUR: Bearish" in message),
        ("GBP Neutral", "GBP: Neutral" in message),
        ("Bot Footer", "EconSentimentBot" in message),
        ("CPI Event", "CPI y/y" in message),
        ("PMI Event", "PMI Manufacturing" in message),
        ("GDP Event", "GDP q/q" in message)
    ]
    
    print("\n✅ Message Format Validation:")
    all_passed = True
    for check_name, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed

def test_empty_report():
    """Test empty report formatting."""
    print("\n🧪 Testing empty report formatting...")
    
    notifier = DiscordNotifier()
    week_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    while week_start.weekday() != 0:  # Monday is 0
        week_start -= timedelta(days=1)
    
    # Format empty message
    message = notifier.format_weekly_report({}, week_start)
    
    print("📊 Generated Empty Report:")
    print("=" * 80)
    print(message)
    print("=" * 80)
    
    # Verify empty report contains expected elements
    checks = [
        ("Header", "📊 Economic Directional Analysis" in message),
        ("No Events Warning", "No high-impact economic events found" in message),
        ("Light Calendar", "Light economic calendar" in message),
        ("Bot Footer", "EconSentimentBot" in message)
    ]
    
    print("\n✅ Empty Report Validation:")
    all_passed = True
    for check_name, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} {check_name}")
        if not passed:
            all_passed = False
    
    return all_passed

def test_webhook_connection():
    """Test webhook connection (if URLs are configured)."""
    print("\n🧪 Testing webhook connections...")
    
    # Check for webhook URLs in environment
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    health_webhook_url = os.getenv("DISCORD_HEALTH_WEBHOOK_URL")
    
    if not webhook_url and not health_webhook_url:
        print("⚠️  No webhook URLs configured in environment variables")
        print("   Set DISCORD_WEBHOOK_URL and/or DISCORD_HEALTH_WEBHOOK_URL to test connections")
        return True
    
    # Create notifier with environment URLs
    notifier = DiscordNotifier()
    
    # Test connections
    results = notifier.test_connection()
    
    print("🔗 Webhook Connection Results:")
    all_passed = True
    for webhook_type, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"  {status} {webhook_type}")
        if not success:
            all_passed = False
    
    return all_passed

def main():
    """Run all Discord notification tests."""
    print("🚀 Discord Notification Demo & Test Suite")
    print("=" * 50)
    
    tests = [
        ("Message Formatting", test_message_formatting),
        ("Empty Report", test_empty_report),
        ("Webhook Connection", test_webhook_connection)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result, None))
        except Exception as e:
            results.append((test_name, False, str(e)))
    
    # Summary
    print("\n" + "=" * 50)
    print("📋 Test Summary:")
    
    passed_count = 0
    for test_name, passed, error in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status} {test_name}")
        if error:
            print(f"    Error: {error}")
        if passed:
            passed_count += 1
    
    print(f"\n🎯 Results: {passed_count}/{len(results)} tests passed")
    
    if passed_count == len(results):
        print("🎉 All tests passed! Discord notification system is ready.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 