#!/usr/bin/env python3
"""
Script to check database content and identify data flow issues
"""
from src.database.config import engine
import pandas as pd

def check_database_content():
    """Check what data is stored in the database"""
    try:
        with engine.connect() as conn:
            # Check events table
            events_df = pd.read_sql('''
                SELECT currency, event_name, scheduled_datetime, impact_level 
                FROM events 
                ORDER BY scheduled_datetime
            ''', conn)
            
            print('=== EVENTS IN DATABASE ===')
            print(f'Total events: {len(events_df)}')
            print(events_df.to_string())
            
            print('\n=== EVENTS BY CURRENCY ===')
            currency_counts = events_df['currency'].value_counts()
            print(currency_counts)
            
            # Check indicators table
            indicators_df = pd.read_sql('''
                SELECT e.currency, e.event_name, i.previous_value, i.forecast_value, i.timestamp_collected
                FROM indicators i
                JOIN events e ON i.event_id = e.id
                ORDER BY i.timestamp_collected DESC
            ''', conn)
            
            print(f'\n=== INDICATORS IN DATABASE ===')
            print(f'Total indicators: {len(indicators_df)}')
            print(indicators_df.to_string())
            
            # Check sentiments table
            sentiments_df = pd.read_sql('''
                SELECT currency, final_sentiment, week_start, week_end, computed_at
                FROM sentiments
                ORDER BY computed_at DESC
            ''', conn)
            
            print(f'\n=== SENTIMENTS IN DATABASE ===')
            print(f'Total sentiments: {len(sentiments_df)}')
            print(sentiments_df.to_string())
            
            return {
                'events': len(events_df),
                'indicators': len(indicators_df), 
                'sentiments': len(sentiments_df),
                'currencies': list(currency_counts.index)
            }
            
    except Exception as e:
        print(f"Error checking database: {e}")
        return None

if __name__ == "__main__":
    check_database_content() 