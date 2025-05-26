#!/usr/bin/env python3
"""
Script to check economic indicators in the database.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database.config import SessionLocal
from sqlalchemy import text

def check_indicators():
    """Check what indicators are in the database."""
    try:
        session = SessionLocal()
        try:
            # Get all distinct event names
            result = session.execute(text('''
                SELECT DISTINCT event_name FROM events ORDER BY event_name
            '''))
            
            print('Current economic indicators in database:')
            print('-' * 50)
            for row in result:
                print(f'- {row[0]}')
            
            print('\n' + '=' * 50)
            
            # Get sample data with dates
            result = session.execute(text('''
                SELECT e.currency, e.event_name, e.scheduled_datetime, i.previous_value, i.forecast_value
                FROM events e 
                JOIN indicators i ON e.id = i.event_id 
                ORDER BY e.scheduled_datetime, e.currency
            '''))
            
            print('Sample data with dates:')
            print('-' * 80)
            for row in result:
                date_str = row[2].strftime('%Y-%m-%d %H:%M') if row[2] else 'N/A'
                print(f'{row[0]:3} | {date_str:16} | {row[1][:30]:30} | Prev={row[3]} | Forecast={row[4]}')
                
        finally:
            session.close()
                
    except Exception as e:
        print(f"Error checking database: {e}")

if __name__ == "__main__":
    check_indicators() 