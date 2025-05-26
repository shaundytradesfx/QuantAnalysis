#!/usr/bin/env python3
"""
Fix timestamp comparison issue
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from datetime import datetime, timedelta
from sqlalchemy import text
from src.database.config import SessionLocal

def fix_timestamp_issue():
    """Fix timestamp comparison in sentiment engine"""
    
    current_time = datetime.utcnow()
    print(f"Current UTC time: {current_time}")
    
    with SessionLocal() as db:
        # Check the exact timestamp comparison issue
        print("\n=== DETAILED TIMESTAMP ANALYSIS ===")
        
        # Get the problematic indicators
        problem_query = text("""
            SELECT 
                event_id,
                timestamp_collected,
                timestamp_collected AT TIME ZONE 'UTC' as utc_timestamp,
                :current_time as current_utc,
                timestamp_collected <= :current_time as is_valid,
                timestamp_collected::timestamp <= :current_time::timestamp as is_valid_no_tz
            FROM indicators 
            WHERE event_id IN (9, 10)
            ORDER BY event_id, timestamp_collected DESC
        """)
        
        result = db.execute(problem_query, {"current_time": current_time}).fetchall()
        
        for row in result:
            print(f"\nEvent {row.event_id}:")
            print(f"  timestamp_collected: {row.timestamp_collected}")
            print(f"  UTC conversion: {row.utc_timestamp}")
            print(f"  Current UTC: {row.current_utc}")
            print(f"  Is valid (with TZ): {row.is_valid}")
            print(f"  Is valid (no TZ): {row.is_valid_no_tz}")
        
        # Try fixing by using timezone-aware comparison
        print(f"\n=== TESTING FIXED SUBQUERY ===")
        fixed_subquery = text("""
            SELECT DISTINCT ON (event_id) 
                event_id,
                previous_value,
                forecast_value,
                timestamp_collected
            FROM indicators
            WHERE timestamp_collected AT TIME ZONE 'UTC' <= :current_time
            ORDER BY event_id, timestamp_collected DESC
        """)
        
        fixed_result = db.execute(fixed_subquery, {"current_time": current_time}).fetchall()
        
        print(f"Fixed subquery returned {len(fixed_result)} indicators")
        event_ids_in_fixed = [row.event_id for row in fixed_result]
        print(f"Event IDs in fixed subquery: {sorted(event_ids_in_fixed)}")
        print(f"Missing event 9 in fixed subquery: {9 in event_ids_in_fixed}")
        print(f"Missing event 10 in fixed subquery: {10 in event_ids_in_fixed}")
        
        # Test the complete fixed query
        print(f"\n=== TESTING COMPLETE FIXED QUERY ===")
        week_start = datetime(2025, 5, 26, 0, 0, 0)
        week_end = datetime(2025, 6, 1, 23, 59, 59)
        
        complete_fixed_query = text("""
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
                WHERE timestamp_collected AT TIME ZONE 'UTC' <= :current_time
                ORDER BY event_id, timestamp_collected DESC
            ) i ON i.event_id = e.id
            WHERE e.scheduled_datetime BETWEEN :week_start AND :week_end
              AND e.impact_level = 'High'
            ORDER BY e.currency, e.scheduled_datetime
        """)
        
        complete_result = db.execute(complete_fixed_query, {
            "week_start": week_start,
            "week_end": week_end,
            "current_time": current_time
        }).fetchall()
        
        print(f"Complete fixed query returned {len(complete_result)} events")
        usd_events_fixed = [row for row in complete_result if row.currency == 'USD']
        print(f"USD events in fixed query: {len(usd_events_fixed)}")
        for event in usd_events_fixed:
            print(f"  - ID {event.event_id}: {event.event_name}")

if __name__ == "__main__":
    fix_timestamp_issue() 