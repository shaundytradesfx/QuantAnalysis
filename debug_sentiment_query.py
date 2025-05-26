#!/usr/bin/env python3
"""
Debug script to check the SQL query used by sentiment engine
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from datetime import datetime, timedelta
from sqlalchemy import text
from src.database.config import SessionLocal
from src.analysis.sentiment_engine import SentimentCalculator

def debug_sentiment_query():
    """Debug the sentiment engine SQL query"""
    
    # Get current week bounds like the sentiment engine does
    calc = SentimentCalculator()
    week_start, week_end = calc.get_current_week_bounds()
    
    print(f"Week bounds: {week_start} to {week_end}")
    
    # Run the exact same query as the sentiment engine
    with SessionLocal() as db:
        query = text("""
            SELECT 
                e.id as event_id,
                e.currency,
                e.event_name,
                e.scheduled_datetime,
                e.impact_level,
                i.previous_value,
                i.forecast_value,
                i.timestamp_collected
            FROM events e
            JOIN (
                SELECT DISTINCT ON (event_id) 
                    event_id,
                    previous_value,
                    forecast_value,
                    timestamp_collected
                FROM indicators
                WHERE timestamp_collected <= :current_time
                ORDER BY event_id, timestamp_collected DESC
            ) i ON i.event_id = e.id
            WHERE e.scheduled_datetime BETWEEN :week_start AND :week_end
              AND e.impact_level = 'High'
            ORDER BY e.currency, e.scheduled_datetime
        """)
        
        result = db.execute(query, {
            "week_start": week_start,
            "week_end": week_end,
            "current_time": datetime.utcnow()
        })
        
        print("\n=== EVENTS RETURNED BY SENTIMENT ENGINE QUERY ===")
        events = []
        for row in result:
            events.append({
                "event_id": row.event_id,
                "currency": row.currency,
                "event_name": row.event_name,
                "scheduled_datetime": row.scheduled_datetime,
                "previous_value": row.previous_value,
                "forecast_value": row.forecast_value,
                "timestamp_collected": row.timestamp_collected
            })
            print(f"ID {row.event_id}: {row.currency} - {row.event_name} (prev: {row.previous_value}, forecast: {row.forecast_value})")
        
        print(f"\nTotal events found: {len(events)}")
        
        # Check USD events specifically
        usd_events = [e for e in events if e['currency'] == 'USD']
        print(f"\nUSD events: {len(usd_events)}")
        for event in usd_events:
            print(f"  - {event['event_name']} (ID: {event['event_id']})")
        
        # Now check what events exist in the database for USD
        print("\n=== ALL USD EVENTS IN DATABASE ===")
        all_usd_query = text("""
            SELECT e.id, e.event_name, e.scheduled_datetime, e.impact_level
            FROM events e 
            WHERE e.currency = 'USD' 
            ORDER BY e.scheduled_datetime
        """)
        
        all_usd_result = db.execute(all_usd_query)
        for row in all_usd_result:
            print(f"ID {row.id}: {row.event_name} - {row.scheduled_datetime} ({row.impact_level})")
            
        # Check indicators for missing events
        print("\n=== INDICATORS FOR MISSING USD EVENTS ===")
        missing_ids = [9, 10]  # GDP q/q and Core PCE Price Index m/m
        for event_id in missing_ids:
            indicators_query = text("""
                SELECT event_id, previous_value, forecast_value, timestamp_collected
                FROM indicators 
                WHERE event_id = :event_id
                ORDER BY timestamp_collected DESC
            """)
            indicators_result = db.execute(indicators_query, {"event_id": event_id})
            print(f"\nEvent ID {event_id} indicators:")
            for row in indicators_result:
                print(f"  - prev: {row.previous_value}, forecast: {row.forecast_value}, time: {row.timestamp_collected}")

if __name__ == "__main__":
    debug_sentiment_query() 