#!/usr/bin/env python3
"""
Script to get current sentiment data from the backend
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.analysis.sentiment_engine import SentimentCalculator
import json

def main():
    try:
        with SentimentCalculator() as calc:
            sentiments = calc.calculate_weekly_sentiments()
            
            print("Current Sentiment Analysis Results:")
            print("=" * 50)
            
            for currency, data in sentiments.items():
                final_sentiment = data['resolution']['final_sentiment']
                events_count = len(data['events'])
                print(f"{currency}: {final_sentiment} ({events_count} events)")
                
                # Show individual events
                for event in data['events']:
                    event_name = event['event_name']
                    sentiment = event['sentiment']
                    print(f"  - {event_name}: {sentiment}")
                print()
            
            # Also output as JSON for frontend update
            print("\nJSON for frontend update:")
            print("=" * 50)
            
            frontend_data = []
            for currency, data in sentiments.items():
                week_start = data['analysis_period']['week_start'][:10]
                week_end = data['analysis_period']['week_end'][:10]
                
                frontend_data.append({
                    "currency": currency,
                    "final_sentiment": data['resolution']['final_sentiment'],
                    "week_start": week_start,
                    "week_end": week_end,
                    "events": [
                        {
                            "event_name": event['event_name'],
                            "sentiment": event['sentiment'],
                            "sentiment_label": event['sentiment_label'],
                            "previous_value": event.get('previous_value'),
                            "forecast_value": event.get('forecast_value')
                        }
                        for event in data['events']
                    ],
                    "computed_at": "2025-06-02T15:00:00Z"
                })
            
            print(json.dumps(frontend_data, indent=2))
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 