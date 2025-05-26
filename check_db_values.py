#!/usr/bin/env python3
"""
Script to check database values for previous and forecast data.
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database.config import SessionLocal
from src.database.models import Event, Indicator
from sqlalchemy import text

def check_database_values():
    """Check what values are stored in the database."""
    try:
        session = SessionLocal()
        try:
            # Check recent indicators data
            result = session.execute(text('''
                SELECT e.currency, e.event_name, i.previous_value, i.forecast_value, i.timestamp_collected
                FROM events e 
                JOIN indicators i ON e.id = i.event_id 
                ORDER BY i.timestamp_collected DESC 
                LIMIT 15
            '''))
            
            print('Recent indicators data:')
            print('-' * 80)
            for row in result:
                print(f'{row.currency:3} - {row.event_name[:30]:30} | Prev={row.previous_value} | Forecast={row.forecast_value}')
            
            print('\n' + '=' * 80)
            
            # Check for NULL values
            null_result = session.execute(text('''
                SELECT COUNT(*) as total_indicators,
                       SUM(CASE WHEN i.previous_value IS NULL THEN 1 ELSE 0 END) as null_previous,
                       SUM(CASE WHEN i.forecast_value IS NULL THEN 1 ELSE 0 END) as null_forecast
                FROM indicators i
            '''))
            
            for row in null_result:
                print(f'Total indicators: {row.total_indicators}')
                print(f'NULL previous values: {row.null_previous}')
                print(f'NULL forecast values: {row.null_forecast}')
                
        finally:
            session.close()
                
    except Exception as e:
        print(f"Error checking database: {e}")

if __name__ == "__main__":
    check_database_values() 