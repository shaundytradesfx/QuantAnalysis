#!/usr/bin/env python3
"""
Script to re-run sentiment calculation with latest data
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.analysis.sentiment_engine import SentimentCalculator
from src.utils.logging import get_logger

logger = get_logger(__name__)

def main():
    """Re-run sentiment calculation with current data"""
    try:
        # Re-run sentiment calculation with current data
        with SentimentCalculator() as calc:
            logger.info('Re-running sentiment calculation with latest data...')
            results = calc.calculate_weekly_sentiments()
            
            print('=== SENTIMENT CALCULATION RESULTS ===')
            for currency, data in results.items():
                print(f'{currency}: {data["resolution"]["final_sentiment"]} ({len(data["events"])} events)')
                for event in data['events']:
                    print(f'  - {event["event_name"]}: {event["sentiment_label"]}')
                    
            print(f'\nSuccessfully updated sentiments for {len(results)} currencies')
            
    except Exception as e:
        logger.error(f"Error recalculating sentiments: {e}")
        print(f"Error: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main()) 