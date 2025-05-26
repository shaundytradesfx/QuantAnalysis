#!/usr/bin/env python3
"""
Script to create sample data for testing the sentiment analysis functionality.
"""
from src.database.config import SessionLocal
from src.database.models import Event, Indicator
from datetime import datetime, timedelta

def create_sample_data():
    """Create sample events for next week to test sentiment analysis."""
    
    # Create sample events for next week (May 26 - June 1)
    with SessionLocal() as db:
        # Clear existing data
        db.query(Indicator).delete()
        db.query(Event).delete()
        
        # Create sample events for next week
        base_date = datetime(2025, 5, 26)  # Monday May 26
        
        events_data = [
            {'currency': 'USD', 'event_name': 'CPI y/y', 'day_offset': 1, 'hour': 14, 'minute': 30, 'previous': 2.1, 'forecast': 2.3},
            {'currency': 'USD', 'event_name': 'Unemployment Rate', 'day_offset': 2, 'hour': 14, 'minute': 30, 'previous': 3.8, 'forecast': 3.7},
            {'currency': 'EUR', 'event_name': 'PMI Manufacturing', 'day_offset': 3, 'hour': 10, 'minute': 0, 'previous': 49.2, 'forecast': 48.8},
            {'currency': 'GBP', 'event_name': 'GDP q/q', 'day_offset': 4, 'hour': 9, 'minute': 30, 'previous': 0.2, 'forecast': 0.3},
            {'currency': 'JPY', 'event_name': 'Interest Rate Decision', 'day_offset': 5, 'hour': 3, 'minute': 0, 'previous': -0.1, 'forecast': -0.1},
            {'currency': 'AUD', 'event_name': 'Employment Change', 'day_offset': 1, 'hour': 23, 'minute': 30, 'previous': 15000, 'forecast': 20000},
            {'currency': 'CAD', 'event_name': 'Inflation Rate', 'day_offset': 2, 'hour': 13, 'minute': 30, 'previous': 2.8, 'forecast': 2.6},
        ]
        
        for event_data in events_data:
            # Create event
            scheduled_dt = base_date + timedelta(days=event_data['day_offset'], hours=event_data['hour'], minutes=event_data['minute'])
            
            event = Event(
                currency=event_data['currency'],
                event_name=event_data['event_name'],
                scheduled_datetime=scheduled_dt,
                impact_level='High'
            )
            db.add(event)
            db.flush()
            
            # Create indicator
            indicator = Indicator(
                event_id=event.id,
                previous_value=event_data['previous'],
                forecast_value=event_data['forecast'],
                timestamp_collected=datetime.utcnow()
            )
            db.add(indicator)
        
        db.commit()
        
        # Verify data
        total_events = db.query(Event).count()
        total_indicators = db.query(Indicator).count()
        print(f'Created {total_events} events and {total_indicators} indicators for next week')
        
        # Show sample events
        sample_events = db.query(Event).all()
        for event in sample_events:
            indicators = [i for i in event.indicators]
            if indicators:
                indicator = indicators[0]
                print(f'  {event.scheduled_datetime} - {event.currency} - {event.event_name} - Prev: {indicator.previous_value}, Forecast: {indicator.forecast_value}')

if __name__ == "__main__":
    create_sample_data() 