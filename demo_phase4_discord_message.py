#!/usr/bin/env python3
"""
Demo script to show Phase 4 enhanced Discord message formatting.
Displays a sample Discord report with actual sentiment data, accuracy metrics, and surprises.
"""
import sys
import os
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def main():
    """Generate and display a sample Phase 4 Discord message."""
    print("🎯 Phase 4 Discord Message Demo")
    print("=" * 50)
    
    try:
        from src.discord.notifier import DiscordNotifier
        
        # Create realistic sample data with actual sentiment information
        sample_data = {
            "USD": {
                "currency": "USD",
                "final_sentiment": "Bullish",
                "actual_sentiment": "Bearish",  # Surprise! Forecast was wrong
                "forecast_accuracy": 66.7,
                "actual_available": True,
                "events": [
                    {
                        "event_name": "CPI y/y",
                        "previous_value": 2.1,
                        "forecast_value": 2.3,
                        "actual_value": 2.0,  # Lower than forecast
                        "sentiment": 1,
                        "sentiment_label": "Bullish",
                        "actual_sentiment": -1,
                        "actual_sentiment_label": "Bearish",
                        "accuracy": "mismatch",
                        "actual_available": True,
                        "data_available": True
                    },
                    {
                        "event_name": "Unemployment Rate",
                        "previous_value": 3.7,
                        "forecast_value": 3.6,
                        "actual_value": 3.5,  # Better than forecast
                        "sentiment": 1,
                        "sentiment_label": "Bullish",
                        "actual_sentiment": 1,
                        "actual_sentiment_label": "Bullish",
                        "accuracy": "match",
                        "actual_available": True,
                        "data_available": True
                    },
                    {
                        "event_name": "ISM Manufacturing PMI",
                        "previous_value": 48.7,
                        "forecast_value": 49.3,
                        "actual_value": 48.9,
                        "sentiment": 1,
                        "sentiment_label": "Bullish",
                        "actual_sentiment": -1,
                        "actual_sentiment_label": "Bearish",
                        "accuracy": "mismatch",
                        "actual_available": True,
                        "data_available": True
                    }
                ]
            },
            "EUR": {
                "currency": "EUR",
                "final_sentiment": "Bullish",
                "actual_sentiment": "Bullish",  # Forecast was correct
                "forecast_accuracy": 100.0,
                "actual_available": True,
                "events": [
                    {
                        "event_name": "ECB Rate Decision",
                        "previous_value": 2.4,
                        "forecast_value": 2.15,
                        "actual_value": 2.15,  # Exactly as forecast
                        "sentiment": 1,
                        "sentiment_label": "Bullish",
                        "actual_sentiment": 1,
                        "actual_sentiment_label": "Bullish",
                        "accuracy": "match",
                        "actual_available": True,
                        "data_available": True
                    }
                ]
            },
            "GBP": {
                "currency": "GBP",
                "final_sentiment": "Neutral",
                "actual_sentiment": "Bearish",  # Worse than expected
                "forecast_accuracy": 0.0,
                "actual_available": True,
                "events": [
                    {
                        "event_name": "GDP q/q",
                        "previous_value": 0.2,
                        "forecast_value": 0.2,
                        "actual_value": 0.1,  # Worse than forecast
                        "sentiment": 0,
                        "sentiment_label": "Neutral",
                        "actual_sentiment": -1,
                        "actual_sentiment_label": "Bearish",
                        "accuracy": "mismatch",
                        "actual_available": True,
                        "data_available": True
                    }
                ]
            }
        }
        
        # Initialize notifier with all Phase 4 features enabled
        notifier = DiscordNotifier()
        notifier.include_actual_sentiment = True
        notifier.show_forecast_accuracy = True
        notifier.show_surprises = True
        
        # Generate message for current week
        week_start = datetime(2024, 12, 2)  # Monday
        message = notifier.format_weekly_report(sample_data, week_start)
        
        print("📨 Generated Discord Message:")
        print("-" * 50)
        print(message)
        print("-" * 50)
        
        print("\n🎯 Phase 4 Features Demonstrated:")
        print("✅ Forecast vs Actual sentiment comparison (USD: Bullish → Bearish)")
        print("✅ Accuracy indicators (✅ for EUR match, ❌ for USD/GBP mismatches)")
        print("✅ Overall forecast accuracy calculation (55% average)")
        print("✅ Per-currency accuracy breakdown with color coding")
        print("✅ Market surprises section highlighting major mismatches")
        print("✅ Forecast (F:) and Actual (A:) values in key events")
        print("✅ Visual indicators and emojis for quick assessment")
        
        print("\n🚀 Ready for Discord webhook integration!")
        
    except Exception as e:
        print(f"❌ Error generating demo message: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 