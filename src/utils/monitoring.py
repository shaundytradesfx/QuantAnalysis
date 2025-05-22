"""
Monitoring utilities for the Forex Factory Sentiment Analyzer.
"""
import os
import time
import json
from functools import wraps
from datetime import datetime

from src.utils.logging import get_logger
from src.database.config import SessionLocal
from src.database.models import Config

logger = get_logger(__name__)

def timing_decorator(func):
    """
    Decorator to measure execution time of a function.
    
    Args:
        func: The function to measure.
        
    Returns:
        function: The wrapped function.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"Function {func.__name__} executed in {execution_time:.2f} seconds")
        return result
    return wrapper

def track_scraper_run(events_count=0, success=True, error_message=None):
    """
    Track a scraper run in the database.
    
    Args:
        events_count (int): Number of events processed.
        success (bool): Whether the run was successful.
        error_message (str, optional): Error message if the run failed.
    """
    try:
        timestamp = datetime.utcnow().isoformat()
        run_data = {
            "timestamp": timestamp,
            "events_count": events_count,
            "success": success,
            "error_message": error_message
        }
        
        # Get existing run history or create new
        with SessionLocal() as db:
            config = db.query(Config).filter(Config.key == "SCRAPER_RUN_HISTORY").first()
            
            if config:
                # Parse existing history
                history = json.loads(config.value)
                # Add new run
                history.append(run_data)
                # Keep only last 10 runs
                if len(history) > 10:
                    history = history[-10:]
                # Update config
                config.value = json.dumps(history)
            else:
                # Create new history
                config = Config(
                    key="SCRAPER_RUN_HISTORY",
                    value=json.dumps([run_data])
                )
                db.add(config)
            
            db.commit()
            
        logger.info(f"Tracked scraper run: {run_data}")
        
    except Exception as e:
        logger.error(f"Failed to track scraper run: {str(e)}")

def get_last_successful_run():
    """
    Get the timestamp of the last successful scraper run.
    
    Returns:
        str: ISO formatted timestamp of the last successful run, or None if no successful runs.
    """
    try:
        with SessionLocal() as db:
            config = db.query(Config).filter(Config.key == "SCRAPER_RUN_HISTORY").first()
            
            if not config:
                return None
                
            history = json.loads(config.value)
            
            # Find the last successful run
            for run in reversed(history):
                if run.get("success", False):
                    return run.get("timestamp")
                    
            return None
            
    except Exception as e:
        logger.error(f"Failed to get last successful run: {str(e)}")
        return None

def check_scraper_health():
    """
    Check if the scraper is healthy based on the last successful run.
    
    Returns:
        bool: True if the scraper is healthy, False otherwise.
    """
    try:
        last_success = get_last_successful_run()
        
        if not last_success:
            logger.warning("No successful scraper runs found")
            return False
            
        # Parse timestamp
        last_success_time = datetime.fromisoformat(last_success)
        current_time = datetime.utcnow()
        
        # Check if the last successful run was within the last 24 hours
        time_diff = current_time - last_success_time
        
        if time_diff.total_seconds() > 24 * 60 * 60:  # 24 hours in seconds
            logger.warning(f"Last successful scraper run was more than 24 hours ago: {last_success}")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Failed to check scraper health: {str(e)}")
        return False 