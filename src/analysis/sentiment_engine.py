"""
Sentiment calculation engine for Forex Factory economic indicators.
"""
import os
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text
from dotenv import load_dotenv

from src.database.config import SessionLocal
from src.database.models import Event, Indicator, Sentiment
from src.utils.logging import get_logger
from src.utils.monitoring import timing_decorator

# Load environment variables
load_dotenv()

logger = get_logger(__name__)

class SentimentCalculator:
    """
    Main sentiment calculation engine.
    """
    
    def __init__(self, db_session: Optional[Session] = None, threshold: float = None):
        """
        Initialize the sentiment calculator.
        
        Args:
            db_session (Session, optional): Database session. If None, creates a new one.
            threshold (float, optional): Sentiment threshold delta. If None, uses environment variable.
        """
        self.db = db_session
        self.threshold = threshold if threshold is not None else float(os.getenv("SENTIMENT_THRESHOLD", "0.0"))
        self.close_db_on_exit = db_session is None
        
        if self.db is None:
            self.db = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.close_db_on_exit and self.db:
            self.db.close()
    
    def get_current_week_bounds(self) -> Tuple[datetime, datetime]:
        """
        Get the start and end of the current week (Monday to Sunday UTC).
        
        Returns:
            Tuple[datetime, datetime]: Week start and end datetimes.
        """
        now = datetime.utcnow()
        
        # Find the Monday of this week
        days_since_monday = now.weekday()
        week_start = now - timedelta(days=days_since_monday)
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Find the Sunday of this week
        week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        
        return week_start, week_end
    
    def get_week_events_with_indicators(self, week_start: datetime, week_end: datetime) -> List[Dict[str, Any]]:
        """
        Retrieve all high-impact events for the specified week with their latest indicators.
        
        Args:
            week_start (datetime): Start of the week.
            week_end (datetime): End of the week.
            
        Returns:
            List[Dict[str, Any]]: List of events with indicators.
        """
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
        
        result = self.db.execute(query, {
            "week_start": week_start,
            "week_end": week_end,
            "current_time": datetime.utcnow()
        })
        
        events = []
        for row in result:
            events.append({
                "event_id": row.event_id,
                "currency": row.currency,
                "event_name": row.event_name,
                "scheduled_datetime": row.scheduled_datetime,
                "impact_level": row.impact_level,
                "previous_value": row.previous_value,
                "forecast_value": row.forecast_value,
                "timestamp_collected": row.timestamp_collected
            })
        
        return events
    
    def calculate_event_sentiment(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate sentiment for a single event.
        
        Args:
            event (Dict[str, Any]): Event data with indicators.
            
        Returns:
            Dict[str, Any]: Event with calculated sentiment.
        """
        previous = event.get("previous_value")
        forecast = event.get("forecast_value")
        
        # Initialize sentiment data
        sentiment_data = {
            "event_id": event["event_id"],
            "event_name": event["event_name"],
            "previous_value": previous,
            "forecast_value": forecast,
            "sentiment": 0,  # Default neutral
            "sentiment_label": "Neutral",
            "data_available": True,
            "reason": None
        }
        
        # Check if we have both values
        if previous is None or forecast is None:
            sentiment_data.update({
                "sentiment": 0,
                "sentiment_label": "Neutral",
                "data_available": False,
                "reason": "Missing forecast or previous value"
            })
            return sentiment_data
        
        # Calculate the difference
        difference = forecast - previous
        
        # Apply threshold logic
        if difference > self.threshold:
            sentiment_data.update({
                "sentiment": 1,
                "sentiment_label": "Bullish"
            })
        elif difference < -self.threshold:
            sentiment_data.update({
                "sentiment": -1,
                "sentiment_label": "Bearish"
            })
        else:
            sentiment_data.update({
                "sentiment": 0,
                "sentiment_label": "Neutral"
            })
        
        return sentiment_data
    
    def resolve_currency_conflicts(self, currency_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Resolve conflicts when multiple events exist for a currency.
        
        Args:
            currency_events (List[Dict[str, Any]]): All events for a currency.
            
        Returns:
            Dict[str, Any]: Final sentiment resolution for the currency.
        """
        if not currency_events:
            return {
                "final_sentiment": "Neutral",
                "final_sentiment_value": 0,
                "reason": "No events found",
                "event_count": 0,
                "sentiment_breakdown": {"bullish": 0, "bearish": 0, "neutral": 0}
            }
        
        # Count sentiments
        sentiment_counts = {"bullish": 0, "bearish": 0, "neutral": 0}
        
        for event in currency_events:
            sentiment = event.get("sentiment", 0)
            if sentiment > 0:
                sentiment_counts["bullish"] += 1
            elif sentiment < 0:
                sentiment_counts["bearish"] += 1
            else:
                sentiment_counts["neutral"] += 1
        
        total_events = len(currency_events)
        
        # Apply conflict resolution rules
        if sentiment_counts["bullish"] > sentiment_counts["bearish"] and sentiment_counts["bullish"] > sentiment_counts["neutral"]:
            final_sentiment = "Bullish"
            final_value = 1
            reason = f"Majority bullish ({sentiment_counts['bullish']}/{total_events} events)"
        elif sentiment_counts["bearish"] > sentiment_counts["bullish"] and sentiment_counts["bearish"] > sentiment_counts["neutral"]:
            final_sentiment = "Bearish"
            final_value = -1
            reason = f"Majority bearish ({sentiment_counts['bearish']}/{total_events} events)"
        elif sentiment_counts["neutral"] > sentiment_counts["bullish"] and sentiment_counts["neutral"] > sentiment_counts["bearish"]:
            final_sentiment = "Neutral"
            final_value = 0
            reason = f"Majority neutral ({sentiment_counts['neutral']}/{total_events} events)"
        else:
            # Handle ties
            if sentiment_counts["bearish"] >= sentiment_counts["bullish"]:
                final_sentiment = "Bearish with Consolidation"
                final_value = -1
                reason = f"Tie resolved bearish ({sentiment_counts['bearish']} bearish, {sentiment_counts['bullish']} bullish, {sentiment_counts['neutral']} neutral)"
            else:
                final_sentiment = "Bullish with Consolidation"
                final_value = 1
                reason = f"Tie resolved bullish ({sentiment_counts['bullish']} bullish, {sentiment_counts['bearish']} bearish, {sentiment_counts['neutral']} neutral)"
        
        return {
            "final_sentiment": final_sentiment,
            "final_sentiment_value": final_value,
            "reason": reason,
            "event_count": total_events,
            "sentiment_breakdown": sentiment_counts
        }
    
    def persist_sentiments(self, currency_sentiments: Dict[str, Any], week_start: datetime, week_end: datetime):
        """
        Persist calculated sentiments to the database.
        
        Args:
            currency_sentiments (Dict[str, Any]): Calculated sentiments by currency.
            week_start (datetime): Start of the analysis week.
            week_end (datetime): End of the analysis week.
        """
        try:
            for currency, sentiment_data in currency_sentiments.items():
                # Create sentiment record
                sentiment_record = Sentiment(
                    currency=currency,
                    week_start=week_start.date(),
                    week_end=week_end.date(),
                    final_sentiment=sentiment_data["resolution"]["final_sentiment"],
                    details_json=sentiment_data,
                    computed_at=datetime.utcnow()
                )
                
                # Check if record already exists for this week
                existing = self.db.query(Sentiment).filter(
                    Sentiment.currency == currency,
                    Sentiment.week_start == week_start.date(),
                    Sentiment.week_end == week_end.date()
                ).first()
                
                if existing:
                    # Update existing record
                    existing.final_sentiment = sentiment_data["resolution"]["final_sentiment"]
                    existing.details_json = sentiment_data
                    existing.computed_at = datetime.utcnow()
                    logger.info(f"Updated sentiment for {currency}: {sentiment_data['resolution']['final_sentiment']}")
                else:
                    # Create new record
                    self.db.add(sentiment_record)
                    logger.info(f"Created sentiment for {currency}: {sentiment_data['resolution']['final_sentiment']}")
            
            self.db.commit()
            logger.info(f"Successfully persisted sentiments for {len(currency_sentiments)} currencies")
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to persist sentiments: {str(e)}")
            raise
    
    @timing_decorator
    def calculate_weekly_sentiments(self, week_start: datetime = None, week_end: datetime = None) -> Dict[str, Any]:
        """
        Calculate sentiments for all currencies for the specified week.
        
        Args:
            week_start (datetime, optional): Start of week. If None, uses current week.
            week_end (datetime, optional): End of week. If None, uses current week.
            
        Returns:
            Dict[str, Any]: Calculated sentiments by currency.
        """
        # Use current week if not specified
        if week_start is None or week_end is None:
            week_start, week_end = self.get_current_week_bounds()
        
        logger.info(f"Calculating sentiments for week {week_start.date()} to {week_end.date()}")
        
        # Get all events for the week
        events = self.get_week_events_with_indicators(week_start, week_end)
        logger.info(f"Retrieved {len(events)} high-impact events for analysis")
        
        if not events:
            logger.warning("No events found for the specified week")
            return {}
        
        # Calculate sentiment for each event
        events_with_sentiment = []
        for event in events:
            sentiment_data = self.calculate_event_sentiment(event)
            events_with_sentiment.append({**event, "sentiment_data": sentiment_data})
        
        # Group by currency
        currency_events = {}
        for event in events_with_sentiment:
            currency = event["currency"]
            if currency not in currency_events:
                currency_events[currency] = []
            currency_events[currency].append(event["sentiment_data"])
        
        # Calculate final sentiments per currency
        currency_sentiments = {}
        for currency, events in currency_events.items():
            resolution = self.resolve_currency_conflicts(events)
            currency_sentiments[currency] = {
                "currency": currency,
                "events": events,
                "resolution": resolution,
                "analysis_period": {
                    "week_start": week_start.isoformat(),
                    "week_end": week_end.isoformat()
                }
            }
        
        # Persist to database
        self.persist_sentiments(currency_sentiments, week_start, week_end)
        
        logger.info(f"Completed sentiment analysis for {len(currency_sentiments)} currencies")
        return currency_sentiments 