"""
Script to run the Forex Factory scraper.
"""
import sys
import argparse
import traceback
from contextlib import contextmanager

from src.scraper.forex_factory import ForexFactoryScraper
from src.scraper.db_manager import ScraperDBManager
from src.database.config import SessionLocal
from src.utils.logging import get_logger
from src.utils.monitoring import timing_decorator, track_scraper_run

logger = get_logger(__name__)

@contextmanager
def get_db_session():
    """
    Context manager for database session.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()

@timing_decorator
def run_scraper():
    """
    Run the Forex Factory scraper.
    
    Returns:
        int: 0 for success, 1 for failure.
    """
    logger.info("Starting Forex Factory scraper...")
    events_count = 0
    success = False
    error_message = None
    
    try:
        # Initialize scraper
        scraper = ForexFactoryScraper()
        
        # Scrape data
        events_data = scraper.scrape_calendar()
        
        if not events_data:
            error_message = "No events found or failed to scrape."
            logger.warning(error_message)
            track_scraper_run(events_count=0, success=False, error_message=error_message)
            return 1
        
        logger.info(f"Scraped {len(events_data)} events.")
        
        # Process data
        with get_db_session() as db:
            db_manager = ScraperDBManager(db)
            processed_count = db_manager.process_events(events_data)
        
        events_count = processed_count
        success = True
        logger.info(f"Successfully processed {processed_count} events.")
        
        # Track successful run
        track_scraper_run(events_count=events_count, success=True)
        return 0
        
    except Exception as e:
        error_message = f"Error running scraper: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_message)
        
        # Track failed run
        track_scraper_run(events_count=events_count, success=False, error_message=error_message)
        return 1

def run_scraper_cli():
    """
    CLI entry point for the scraper.
    """
    parser = argparse.ArgumentParser(description="Run the Forex Factory scraper.")
    parser.add_argument("--force", action="store_true", help="Force scraper to run regardless of schedule")
    args = parser.parse_args()
    
    sys.exit(run_scraper())

if __name__ == "__main__":
    run_scraper_cli() 