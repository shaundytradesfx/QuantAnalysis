#!/usr/bin/env python3
"""
Debug timezone issue in sentiment engine
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from datetime import datetime, timedelta
from sqlalchemy import text
from src.database.config import SessionLocal
from src.analysis.sentiment_engine import SentimentCalculator

def debug_timezone_issue():
    """Debug timezone handling in sentiment engine"""
    
    # Get current week bounds like the sentiment engine does
    calc = SentimentCalculator()
    week_start, week_end = calc.get_current_week_bounds()
    
    print(f"Week bounds (UTC): {week_start} to {week_end}")
    
    with SessionLocal() as db:
        # Check all USD events with timezone info
        print("\n=== ALL USD EVENTS WITH TIMEZONE INFO ===")
        usd_query = text("""
            SELECT 
                id, 
                event_name, 
                scheduled_datetime,
                scheduled_datetime AT TIME ZONE 'UTC' as utc_time,
                CASE 
                    WHEN scheduled_datetime BETWEEN :week_start AND :week_end THEN 'IN RANGE'
                    ELSE 'OUT OF RANGE'
                END as in_range
            FROM events 
            WHERE currency = 'USD' 
            ORDER BY scheduled_datetime
        """)
        
        result = db.execute(usd_query, {
            "week_start": week_start,
            "week_end": week_end
        })
        
        for row in result:
            print(f"ID {row.id}: {row.event_name}")
            print(f"  Original: {row.scheduled_datetime}")
            print(f"  UTC: {row.utc_time}")
            print(f"  Status: {row.in_range}")
            print()
        
        # Check if the missing events have indicators
        print("=== CHECKING INDICATORS FOR MISSING EVENTS ===")
        missing_events = [9, 10]  # Core PCE and GDP q/q
        
        for event_id in missing_events:
            # Check if event exists
            event_query = text("SELECT id, event_name, scheduled_datetime FROM events WHERE id = :id")
            event_result = db.execute(event_query, {"id": event_id}).fetchone()
            
            if event_result:
                print(f"\nEvent ID {event_id}: {event_result.event_name}")
                print(f"Scheduled: {event_result.scheduled_datetime}")
                
                # Check indicators
                indicator_query = text("""
                    SELECT previous_value, forecast_value, timestamp_collected 
                    FROM indicators 
                    WHERE event_id = :event_id 
                    ORDER BY timestamp_collected DESC
                """)
                indicators = db.execute(indicator_query, {"event_id": event_id}).fetchall()
                
                print(f"Indicators found: {len(indicators)}")
                for ind in indicators:
                    print(f"  - prev: {ind.previous_value}, forecast: {ind.forecast_value}, time: {ind.timestamp_collected}")
                    
                # Test the exact join condition
                join_query = text("""
                    SELECT 
                        e.id, e.event_name, e.scheduled_datetime,
                        i.previous_value, i.forecast_value, i.timestamp_collected
                    FROM events e
                    JOIN (
                        SELECT DISTINCT ON (event_id) 
                            event_id, previous_value, forecast_value, timestamp_collected
                        FROM indicators
                        WHERE timestamp_collected <= :current_time
                        ORDER BY event_id, timestamp_collected DESC
                    ) i ON i.event_id = e.id
                    WHERE e.id = :event_id
                """)
                
                join_result = db.execute(join_query, {
                    "event_id": event_id,
                    "current_time": datetime.utcnow()
                }).fetchone()
                
                if join_result:
                    print(f"  JOIN successful: prev={join_result.previous_value}, forecast={join_result.forecast_value}")
                else:
                    print(f"  JOIN failed - no indicators found")

if __name__ == "__main__":
    debug_timezone_issue() 