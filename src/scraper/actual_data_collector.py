"""
Actual data collector for economic events that have already occurred.
Phase 6: Enhanced with comprehensive monitoring and error handling.
"""
import datetime
import time
import random
from typing import List, Dict, Optional, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import text

from src.database.config import SessionLocal
from src.database.models import Event, Indicator
from src.scraper.forex_factory import ForexFactoryScraper
from src.utils.logging import get_logger
from src.utils.actual_data_monitoring import ActualDataMonitor

logger = get_logger(__name__)

class ActualDataCollector:
    """
    Collector for actual economic data after events have occurred.
    Phase 6: Enhanced with monitoring and robust error handling.
    """
    
    def __init__(self, db_session: Optional[Session] = None, lookback_days: int = 7, retry_limit: int = 3):
        """
        Initialize the actual data collector.
        
        Args:
            db_session (Session, optional): Database session. If None, creates a new one.
            lookback_days (int): How far back to check for missing actual data.
            retry_limit (int): Maximum retries for missing actual data.
        """
        self.db = db_session
        self.lookback_days = lookback_days
        self.retry_limit = retry_limit
        self.close_db_on_exit = db_session is None
        self.scraper = ForexFactoryScraper()
        
        # Phase 6: Enhanced error handling and monitoring
        self.monitor = None
        self.network_failure_count = 0
        self.parsing_failure_count = 0
        self.db_failure_count = 0
        self.consecutive_failures = 0
        self.circuit_breaker_threshold = 5  # Stop after 5 consecutive failures
        self.circuit_breaker_open = False
        self.last_failure_time = None
        self.backoff_multiplier = 1.0
        
        if self.db is None:
            self.db = SessionLocal()
    
    def __enter__(self):
        # Phase 6: Initialize monitoring
        self.monitor = ActualDataMonitor(db_session=self.db)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.close_db_on_exit and self.db:
            self.db.close()
        if self.monitor:
            self.monitor.__exit__(exc_type, exc_val, exc_tb)
    
    def get_events_missing_actual_data(self) -> List[Dict[str, Any]]:
        """
        Get all events that are missing actual data and occurred in the past.
        
        Returns:
            List[Dict[str, Any]]: List of event dictionaries missing actual data.
        """
        try:
            cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=self.lookback_days)
            current_time = datetime.datetime.utcnow()
            
            # Query for events that have occurred but don't have actual data
            query = text("""
                SELECT DISTINCT 
                    e.id as event_id,
                    i.id as indicator_id,
                    e.currency,
                    e.event_name,
                    e.scheduled_datetime,
                    e.impact_level,
                    i.previous_value,
                    i.forecast_value,
                    COALESCE(i.is_actual_available, FALSE) as is_actual_available,
                    i.timestamp_collected
                FROM events e
                JOIN (
                    SELECT DISTINCT ON (event_id) *
                    FROM indicators
                    WHERE timestamp_collected <= :current_time
                    ORDER BY event_id, timestamp_collected DESC
                ) i ON i.event_id = e.id
                WHERE e.scheduled_datetime >= :cutoff_date
                  AND e.scheduled_datetime <= :current_time
                  AND e.impact_level = 'High'
                  AND (i.is_actual_available IS NULL OR i.is_actual_available = FALSE)
                ORDER BY e.scheduled_datetime DESC
            """)
            
            result = self.db.execute(query, {
                "cutoff_date": cutoff_date,
                "current_time": current_time
            })
            
            events = []
            for row in result:
                events.append({
                    "event_id": row.event_id,
                    "indicator_id": row.indicator_id,
                    "currency": row.currency,
                    "event_name": row.event_name,
                    "scheduled_datetime": row.scheduled_datetime,
                    "impact_level": row.impact_level,
                    "previous_value": row.previous_value,
                    "forecast_value": row.forecast_value,
                    "is_actual_available": row.is_actual_available,
                    "timestamp_collected": row.timestamp_collected
                })
            
            logger.info(f"Found {len(events)} events missing actual data")
            return events
            
        except Exception as e:
            logger.error(f"Database error getting events missing actual data: {str(e)}")
            self.db_failure_count += 1
            raise
    
    def collect_actual_data_for_event(self, event: Dict[str, Any]) -> Optional[float]:
        """
        Collect actual data for a specific event from Forex Factory.
        Phase 6: Enhanced with robust error handling and retry logic.
        
        Args:
            event (Dict[str, Any]): Event data.
            
        Returns:
            Optional[float]: Actual value if found, None otherwise.
        """
        # Phase 6: Check circuit breaker
        if self._is_circuit_breaker_open():
            logger.warning("Circuit breaker is open, skipping actual data collection")
            return None
        
        retry_count = 0
        while retry_count < self.retry_limit:
            try:
                # Phase 6: Apply exponential backoff for retries
                if retry_count > 0:
                    backoff_time = self._calculate_backoff_time(retry_count)
                    logger.info(f"Retrying actual data collection for {event['currency']} {event['event_name']} in {backoff_time:.2f}s (attempt {retry_count + 1}/{self.retry_limit})")
                    time.sleep(backoff_time)
                
                # Get calendar data from Forex Factory
                calendar_events = self._scrape_with_error_handling()
                
                if not calendar_events:
                    logger.warning("No calendar data retrieved from Forex Factory")
                    retry_count += 1
                    continue
                
                # Find matching event in scraped data
                event_datetime = event["scheduled_datetime"]
                event_name = event["event_name"]
                event_currency = event["currency"]
                
                logger.debug(f"Looking for {event_currency} {event_name} scheduled at {event_datetime}")
                
                # Look for the event in scraped data
                for scraped_event in calendar_events:
                    # Match by currency, event name, and approximate time
                    if (scraped_event.get("currency") == event_currency and
                        self._events_match(event_name, scraped_event.get("event_name", "")) and
                        self._datetimes_match(event_datetime, scraped_event.get("scheduled_datetime"))):
                        
                        actual_value = scraped_event.get("actual_value")
                        if actual_value is not None:
                            logger.info(f"Found actual value {actual_value} for {event_currency} {event_name}")
                            self._record_success()
                            return float(actual_value)
                
                logger.info(f"No actual data found for {event_currency} {event_name}")
                return None
                
            except Exception as e:
                retry_count += 1
                error_msg = f"Error collecting actual data for event {event['event_id']} (attempt {retry_count}/{self.retry_limit}): {str(e)}"
                
                if retry_count < self.retry_limit:
                    logger.warning(error_msg)
                else:
                    logger.error(error_msg)
                    self._record_failure(str(e))
                
                # Categorize the error
                if "network" in str(e).lower() or "timeout" in str(e).lower() or "connection" in str(e).lower():
                    self.network_failure_count += 1
                elif "parsing" in str(e).lower() or "html" in str(e).lower():
                    self.parsing_failure_count += 1
                else:
                    # Generic error
                    pass
        
        return None
    
    def _scrape_with_error_handling(self) -> Optional[List[Dict[str, Any]]]:
        """
        Scrape calendar data with enhanced error handling.
        
        Returns:
            Optional[List[Dict[str, Any]]]: Scraped calendar events or None.
        """
        try:
            return self.scraper.scrape_calendar()
        except Exception as e:
            error_type = "unknown"
            if "network" in str(e).lower() or "timeout" in str(e).lower():
                error_type = "network"
                self.network_failure_count += 1
            elif "parsing" in str(e).lower() or "html" in str(e).lower():
                error_type = "parsing"
                self.parsing_failure_count += 1
            
            logger.error(f"Scraping error ({error_type}): {str(e)}")
            raise
    
    def _calculate_backoff_time(self, retry_count: int) -> float:
        """
        Calculate exponential backoff time with jitter.
        
        Args:
            retry_count (int): Current retry attempt.
            
        Returns:
            float: Backoff time in seconds.
        """
        base_delay = 2 ** retry_count  # Exponential backoff: 2, 4, 8, 16...
        jitter = random.uniform(0.5, 1.5)  # Add jitter to avoid thundering herd
        return min(base_delay * jitter * self.backoff_multiplier, 60)  # Cap at 60 seconds
    
    def _is_circuit_breaker_open(self) -> bool:
        """
        Check if the circuit breaker is open (too many consecutive failures).
        
        Returns:
            bool: True if circuit breaker is open.
        """
        if not self.circuit_breaker_open:
            return False
        
        # Reset circuit breaker after 15 minutes
        if self.last_failure_time and (datetime.datetime.utcnow() - self.last_failure_time).total_seconds() > 900:
            logger.info("Resetting circuit breaker after cooldown period")
            self.circuit_breaker_open = False
            self.consecutive_failures = 0
            self.backoff_multiplier = 1.0
            return False
        
        return True
    
    def _record_success(self) -> None:
        """
        Record a successful operation for circuit breaker management.
        """
        self.consecutive_failures = 0
        self.circuit_breaker_open = False
        self.backoff_multiplier = max(0.5, self.backoff_multiplier * 0.9)  # Reduce backoff on success
    
    def _record_failure(self, error_message: str) -> None:
        """
        Record a failure for circuit breaker management.
        
        Args:
            error_message (str): Error message.
        """
        self.consecutive_failures += 1
        self.last_failure_time = datetime.datetime.utcnow()
        self.backoff_multiplier = min(2.0, self.backoff_multiplier * 1.1)  # Increase backoff on failure
        
        if self.consecutive_failures >= self.circuit_breaker_threshold:
            logger.warning(f"Opening circuit breaker after {self.consecutive_failures} consecutive failures")
            self.circuit_breaker_open = True
    
    def _events_match(self, event_name1: str, event_name2: str) -> bool:
        """
        Check if two event names match (fuzzy matching).
        
        Args:
            event_name1 (str): First event name.
            event_name2 (str): Second event name.
            
        Returns:
            bool: True if events match.
        """
        if not event_name1 or not event_name2:
            return False
        
        # Normalize names
        name1 = event_name1.lower().strip()
        name2 = event_name2.lower().strip()
        
        # Exact match
        if name1 == name2:
            return True
        
        # Remove common variations
        variations = [
            ("m/m", "mom"),
            ("y/y", "yoy"),
            ("q/q", "qoq"),
            ("  ", " "),
            (".", ""),
            (",", "")
        ]
        
        for old, new in variations:
            name1 = name1.replace(old, new)
            name2 = name2.replace(old, new)
        
        # Check if one is contained in the other (for partial matches)
        return name1 in name2 or name2 in name1
    
    def _datetimes_match(self, datetime1: datetime.datetime, datetime2: Optional[datetime.datetime]) -> bool:
        """
        Check if two datetimes match within a reasonable window.
        
        Args:
            datetime1 (datetime.datetime): First datetime.
            datetime2 (Optional[datetime.datetime]): Second datetime.
            
        Returns:
            bool: True if datetimes match within 24 hours.
        """
        if not datetime2:
            return False
        
        # Allow up to 24 hours difference (events can be delayed or rescheduled)
        time_diff = abs((datetime1 - datetime2).total_seconds())
        return time_diff <= 24 * 60 * 60  # 24 hours in seconds
    
    def update_indicator_with_actual_data(self, indicator_id: int, actual_value: float) -> bool:
        """
        Update an indicator record with actual data.
        Phase 6: Enhanced with better error handling and monitoring.
        
        Args:
            indicator_id (int): ID of the indicator to update.
            actual_value (float): The actual value to store.
            
        Returns:
            bool: True if updated successfully.
        """
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                indicator = self.db.query(Indicator).filter(Indicator.id == indicator_id).first()
                if not indicator:
                    logger.error(f"Indicator with ID {indicator_id} not found")
                    return False
                
                # Update the indicator
                indicator.actual_value = actual_value
                indicator.actual_collected_at = datetime.datetime.utcnow()
                indicator.is_actual_available = True
                
                # Calculate actual sentiment (will be done by sentiment engine later)
                # For now, just mark that actual data is available
                
                self.db.commit()
                logger.info(f"Updated indicator {indicator_id} with actual value {actual_value}")
                return True
                
            except Exception as e:
                retry_count += 1
                error_msg = f"Database error updating indicator {indicator_id} (attempt {retry_count}/{max_retries}): {str(e)}"
                
                if retry_count < max_retries:
                    logger.warning(error_msg)
                    self.db.rollback()
                    time.sleep(retry_count * 2)  # Simple backoff for DB retries
                else:
                    logger.error(error_msg)
                    self.db.rollback()
                    self.db_failure_count += 1
                    return False
        
        return False
    
    def collect_all_missing_actual_data(self) -> Tuple[int, int]:
        """
        Collect actual data for all events missing it.
        Phase 6: Enhanced with comprehensive monitoring and error tracking.
        
        Returns:
            Tuple[int, int]: (total_events_processed, successful_updates)
        """
        start_time = time.time()
        
        try:
            events_missing_data = self.get_events_missing_actual_data()
            
            if not events_missing_data:
                logger.info("No events missing actual data")
                # Phase 6: Track the collection attempt
                if self.monitor:
                    execution_time = time.time() - start_time
                    self.monitor.track_collection_attempt(0, 0, True, execution_time)
                return 0, 0
            
            total_processed = len(events_missing_data)
            successful_updates = 0
            
            logger.info(f"Processing {total_processed} events missing actual data")
            
            for i, event in enumerate(events_missing_data, 1):
                logger.debug(f"Processing event {i}/{total_processed}: {event['currency']} {event['event_name']}")
                
                actual_value = self.collect_actual_data_for_event(event)
                
                if actual_value is not None:
                    if self.update_indicator_with_actual_data(event["indicator_id"], actual_value):
                        successful_updates += 1
                        
                        # Phase 6: Track accuracy metrics if we have both forecast and actual
                        if (event.get("forecast_value") is not None and 
                            event.get("previous_value") is not None and 
                            self.monitor):
                            
                            # Calculate forecast and actual sentiment for tracking
                            from src.analysis.sentiment_engine import SentimentCalculator
                            
                            temp_calc = SentimentCalculator(db_session=self.db)
                            forecast_result = temp_calc.calculate_event_sentiment(event)
                            
                            # Create event with actual value for actual sentiment calculation
                            actual_event = event.copy()
                            actual_event["actual_value"] = actual_value
                            actual_event["is_actual_available"] = True
                            actual_result = temp_calc.calculate_actual_event_sentiment(actual_event)
                            
                            # Track accuracy
                            self.monitor.track_accuracy_metrics(
                                currency=event["currency"],
                                forecast_sentiment=forecast_result["sentiment"],
                                actual_sentiment=actual_result["actual_sentiment"],
                                event_name=event["event_name"],
                                forecast_value=event.get("forecast_value"),
                                actual_value=actual_value
                            )
            
            execution_time = time.time() - start_time
            success_rate = (successful_updates / total_processed) * 100 if total_processed > 0 else 0
            
            logger.info(f"Successfully updated {successful_updates} out of {total_processed} events with actual data ({success_rate:.1f}% success rate)")
            logger.info(f"Collection statistics - Network failures: {self.network_failure_count}, Parsing failures: {self.parsing_failure_count}, DB failures: {self.db_failure_count}")
            
            # Phase 6: Track the collection attempt
            if self.monitor:
                overall_success = successful_updates > 0 or total_processed == 0
                error_message = None
                if self.network_failure_count > 0 or self.parsing_failure_count > 0 or self.db_failure_count > 0:
                    error_message = f"Network: {self.network_failure_count}, Parsing: {self.parsing_failure_count}, DB: {self.db_failure_count}"
                
                self.monitor.track_collection_attempt(
                    events_processed=total_processed,
                    events_updated=successful_updates,
                    success=overall_success,
                    execution_time=execution_time,
                    error_message=error_message
                )
            
            return total_processed, successful_updates
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Critical error in collect_all_missing_actual_data: {str(e)}")
            
            # Phase 6: Track the failed collection attempt
            if self.monitor:
                self.monitor.track_collection_attempt(
                    events_processed=0,
                    events_updated=0,
                    success=False,
                    execution_time=execution_time,
                    error_message=str(e)
                )
            
            raise


def collect_actual_data():
    """
    Standalone function to collect actual data for missing events.
    
    Returns:
        Tuple[int, int]: (total_events_processed, successful_updates)
    """
    with ActualDataCollector() as collector:
        return collector.collect_all_missing_actual_data()


if __name__ == "__main__":
    # For testing
    total, successful = collect_actual_data()
    print(f"Processed {total} events, successfully updated {successful} with actual data") 