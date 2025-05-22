"""
Database manager for the scraper.
"""
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime

from src.database.models import Event, Indicator
from src.utils.logging import get_logger

logger = get_logger(__name__)

class ScraperDBManager:
    """
    Database manager for the scraper.
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize the database manager.
        
        Args:
            db_session (Session): SQLAlchemy database session.
        """
        self.db = db_session
    
    def get_or_create_event(self, event_data: Dict[str, Any]) -> Event:
        """
        Get an existing event or create a new one.
        
        Args:
            event_data (Dict[str, Any]): Event data from the scraper.
            
        Returns:
            Event: The event object from the database.
        """
        # Check if event already exists
        existing_event = self.db.query(Event).filter(
            Event.currency == event_data["currency"],
            Event.event_name == event_data["event_name"],
            Event.scheduled_datetime == event_data["scheduled_datetime"]
        ).first()
        
        if existing_event:
            logger.debug(f"Found existing event: {existing_event}")
            return existing_event
        
        # Create new event
        new_event = Event(
            currency=event_data["currency"],
            event_name=event_data["event_name"],
            scheduled_datetime=event_data["scheduled_datetime"],
            impact_level=event_data["impact_level"]
        )
        
        self.db.add(new_event)
        self.db.commit()
        self.db.refresh(new_event)
        
        logger.info(f"Created new event: {new_event}")
        return new_event
    
    def add_or_update_indicator(self, event: Event, previous_value: Optional[float], forecast_value: Optional[float]) -> Indicator:
        """
        Add or update an indicator for an event.
        
        Args:
            event (Event): The event object.
            previous_value (Optional[float]): The previous value.
            forecast_value (Optional[float]): The forecast value.
            
        Returns:
            Indicator: The indicator object from the database.
        """
        # Check if indicator values have changed
        latest_indicator = self.db.query(Indicator).filter(
            Indicator.event_id == event.id
        ).order_by(Indicator.timestamp_collected.desc()).first()
        
        if latest_indicator and latest_indicator.previous_value == previous_value and latest_indicator.forecast_value == forecast_value:
            logger.debug(f"Indicator values unchanged for event: {event}")
            return latest_indicator
        
        # Create new indicator
        new_indicator = Indicator(
            event_id=event.id,
            previous_value=previous_value,
            forecast_value=forecast_value,
            timestamp_collected=datetime.utcnow()
        )
        
        self.db.add(new_indicator)
        self.db.commit()
        self.db.refresh(new_indicator)
        
        logger.info(f"Added new indicator for event: {event}, previous: {previous_value}, forecast: {forecast_value}")
        return new_indicator
    
    def process_events(self, events_data: List[Dict[str, Any]]) -> int:
        """
        Process a list of events from the scraper.
        
        Args:
            events_data (List[Dict[str, Any]]): List of event data from the scraper.
            
        Returns:
            int: Number of events processed.
        """
        processed_count = 0
        
        for event_data in events_data:
            try:
                # Get or create event
                event = self.get_or_create_event(event_data)
                
                # Add or update indicator
                self.add_or_update_indicator(
                    event=event,
                    previous_value=event_data.get("previous_value"),
                    forecast_value=event_data.get("forecast_value")
                )
                
                processed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing event: {event_data}, error: {str(e)}")
                self.db.rollback()
        
        logger.info(f"Processed {processed_count} events.")
        return processed_count 