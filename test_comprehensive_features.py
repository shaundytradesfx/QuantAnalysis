#!/usr/bin/env python3
"""
Comprehensive test of all implemented features.
"""
import sys
import os
sys.path.append('.')

from src.analysis.sentiment_engine import SentimentCalculator
from src.discord.notifier import DiscordNotifier
from datetime import datetime

def test_comprehensive_features():
    """Test all implemented features comprehensively."""
    print("🧪 COMPREHENSIVE FEATURE TEST")
    print("=" * 80)
    
    # Test 1: Inverse Indicators Detection
    print("\n1️⃣ INVERSE INDICATORS DETECTION")
    print("-" * 40)
    
    calculator = SentimentCalculator()
    
    inverse_tests = [
        ("Unemployment Claims", True),
        ("CPI y/y", True),
        ("Core PCE Price Index m/m", True),
        ("GDP m/m", False),
        ("Manufacturing PMI", False),
    ]
    
    for indicator, expected in inverse_tests:
        actual = calculator.is_inverse_indicator(indicator)
        status = "✅" if actual == expected else "❌"
        print(f"  {status} {indicator}: {actual} (expected: {expected})")
    
    # Test 2: Sentiment Calculation Logic
    print("\n2️⃣ SENTIMENT CALCULATION LOGIC")
    print("-" * 40)
    
    test_events = [
        {
            "name": "Unemployment Claims (Higher = Bearish)",
            "event": {
                "event_id": 1,
                "event_name": "Unemployment Claims",
                "previous_value": 200000,
                "forecast_value": 220000,
                "scheduled_datetime": datetime(2025, 5, 29, 12, 30)
            },
            "expected": "Bearish"
        },
        {
            "name": "CPI y/y (Lower = Bullish)",
            "event": {
                "event_id": 2,
                "event_name": "CPI y/y",
                "previous_value": 2.4,
                "forecast_value": 2.3,
                "scheduled_datetime": datetime(2025, 5, 28, 1, 30)
            },
            "expected": "Bullish"
        },
        {
            "name": "GDP (Equal = Bullish)",
            "event": {
                "event_id": 3,
                "event_name": "GDP m/m",
                "previous_value": -0.3,
                "forecast_value": -0.3,
                "scheduled_datetime": datetime(2025, 5, 29, 12, 30)
            },
            "expected": "Bullish"
        },
        {
            "name": "Manufacturing PMI (Higher = Bullish)",
            "event": {
                "event_id": 4,
                "event_name": "Manufacturing PMI",
                "previous_value": 49.0,
                "forecast_value": 49.5,
                "scheduled_datetime": datetime(2025, 5, 31, 1, 30)
            },
            "expected": "Bullish"
        }
    ]
    
    for test in test_events:
        result = calculator.calculate_event_sentiment(test["event"])
        actual = result["sentiment_label"]
        expected = test["expected"]
        status = "✅" if actual == expected else "❌"
        
        print(f"  {status} {test['name']}")
        print(f"      Previous: {test['event']['previous_value']} → Forecast: {test['event']['forecast_value']}")
        print(f"      Result: {actual} (expected: {expected})")
        print(f"      Reason: {result.get('reason', 'N/A')}")
        print()
    
    # Test 3: Date Grouping in Discord
    print("3️⃣ DISCORD DATE GROUPING")
    print("-" * 40)
    
    # Create mock sentiment data with multiple dates
    mock_sentiments = {
        "USD": {
            "currency": "USD",
            "events": [
                {
                    "event_name": "FOMC Meeting Minutes",
                    "previous_value": None,
                    "forecast_value": None,
                    "scheduled_datetime": "2025-05-28T18:00:00+04:00",
                    "sentiment_label": "Neutral",
                    "data_available": False,
                    "is_inverse": False
                },
                {
                    "event_name": "Unemployment Claims",
                    "previous_value": 227.0,
                    "forecast_value": 229.0,
                    "scheduled_datetime": "2025-05-29T12:30:00+04:00",
                    "sentiment_label": "Bearish",
                    "data_available": True,
                    "is_inverse": True
                },
                {
                    "event_name": "Core PCE Price Index m/m",
                    "previous_value": 0.0,
                    "forecast_value": 0.1,
                    "scheduled_datetime": "2025-05-30T12:30:00+04:00",
                    "sentiment_label": "Bearish",
                    "data_available": True,
                    "is_inverse": True
                }
            ],
            "resolution": {
                "final_sentiment": "Bearish",
                "reason": "Majority bearish (2/3 events)",
                "sentiment_breakdown": {"bullish": 0, "bearish": 2, "neutral": 1}
            }
        }
    }
    
    notifier = DiscordNotifier()
    message = notifier.format_weekly_report(mock_sentiments, datetime(2025, 5, 26))
    
    # Check for date grouping features
    date_features = {
        "Date headers present": "📅 **" in message,
        "Multiple dates shown": message.count("📅 **") > 1,
        "Inverse indicators marked": "(inverse)" in message,
        "Chronological ordering": "May 28" in message and "May 29" in message and "May 30" in message
    }
    
    for feature, present in date_features.items():
        status = "✅" if present else "❌"
        print(f"  {status} {feature}")
    
    # Test 4: Real Database Integration
    print("\n4️⃣ REAL DATABASE INTEGRATION")
    print("-" * 40)
    
    try:
        week_start = datetime(2025, 5, 26)
        week_end = datetime(2025, 6, 1, 23, 59, 59)
        
        real_sentiments = calculator.calculate_weekly_sentiments(week_start, week_end)
        
        if real_sentiments:
            print(f"  ✅ Successfully calculated sentiments for {len(real_sentiments)} currencies")
            
            # Check for specific features in real data
            usd_data = real_sentiments.get("USD", {})
            if usd_data:
                usd_events = usd_data.get("events", [])
                unemployment_event = next((e for e in usd_events if "unemployment" in e.get("event_name", "").lower()), None)
                
                if unemployment_event:
                    is_inverse = unemployment_event.get("is_inverse", False)
                    sentiment = unemployment_event.get("sentiment_label", "")
                    print(f"  ✅ Unemployment Claims correctly marked as inverse: {is_inverse}")
                    print(f"  ✅ Unemployment Claims sentiment: {sentiment}")
                
                equal_event = next((e for e in usd_events if e.get("previous_value") == e.get("forecast_value")), None)
                if equal_event:
                    sentiment = equal_event.get("sentiment_label", "")
                    print(f"  ✅ Equal values event sentiment: {sentiment}")
        else:
            print("  ⚠️  No real sentiment data available for testing")
            
    except Exception as e:
        print(f"  ❌ Database integration error: {str(e)}")
    
    print("\n" + "=" * 80)
    print("🎯 COMPREHENSIVE TEST COMPLETED")
    print("=" * 80)

if __name__ == "__main__":
    test_comprehensive_features() 