#!/usr/bin/env python3
"""
Debug timestamp comparison issue
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from datetime import datetime, timedelta
from sqlalchemy import text
from src.database.config import SessionLocal

def debug_timestamp_issue():
    """Debug timestamp comparison in sentiment engine"""
    
    current_time = datetime.utcnow()
    print(f"Current UTC time: {current_time}")
    
    with SessionLocal() as db:
        # Check indicator timestamps for missing events
        print("\n=== INDICATOR TIMESTAMPS FOR MISSING EVENTS ===")
        missing_events = [9, 10]  # Core PCE and GDP q/q
        
        for event_id in missing_events:
            indicator_query = text("""
                SELECT 
                    event_id,
                    previous_value, 
                    forecast_value, 
                    timestamp_collected,
                    timestamp_collected AT TIME ZONE 'UTC' as utc_timestamp,
                    CASE 
                        WHEN timestamp_collected <= :current_time THEN 'VALID'
                        ELSE 'FUTURE'
                    END as time_status
                FROM indicators 
                WHERE event_id = :event_id 
                ORDER BY timestamp_collected DESC
            """)
            
            indicators = db.execute(indicator_query, {
                "event_id": event_id,
                "current_time": current_time
            }).fetchall()
            
            print(f"\nEvent ID {event_id}:")
            for ind in indicators:
                print(f"  - timestamp_collected: {ind.timestamp_collected}")
                print(f"  - UTC timestamp: {ind.utc_timestamp}")
                print(f"  - Status vs current time: {ind.time_status}")
                print(f"  - prev: {ind.previous_value}, forecast: {ind.forecast_value}")
        
        # Test the subquery directly
        print(f"\n=== TESTING SUBQUERY DIRECTLY ===")
        subquery = text("""
            SELECT DISTINCT ON (event_id) 
                event_id,
                previous_value,
                forecast_value,
                timestamp_collected,
                timestamp_collected AT TIME ZONE 'UTC' as utc_timestamp
            FROM indicators
            WHERE timestamp_collected <= :current_time
            ORDER BY event_id, timestamp_collected DESC
        """)
        
        subquery_result = db.execute(subquery, {"current_time": current_time}).fetchall()
        
        print(f"Subquery returned {len(subquery_result)} indicators")
        for row in subquery_result:
            print(f"  Event {row.event_id}: {row.utc_timestamp} (prev: {row.previous_value}, forecast: {row.forecast_value})")
        
        # Check if events 9 and 10 are in the subquery results
        event_ids_in_subquery = [row.event_id for row in subquery_result]
        print(f"\nEvent IDs in subquery: {event_ids_in_subquery}")
        print(f"Missing event 9 in subquery: {9 in event_ids_in_subquery}")
        print(f"Missing event 10 in subquery: {10 in event_ids_in_subquery}")

if __name__ == "__main__":
    debug_timestamp_issue() 