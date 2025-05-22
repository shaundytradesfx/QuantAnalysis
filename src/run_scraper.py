"""
Script to run the Forex Factory scraper.
"""
import sys
import argparse
from contextlib import contextmanager

from src.scraper.forex_factory import ForexFactoryScraper
from src.scraper.db_manager import ScraperDBManager
from src.database.config import SessionLocal
from src.utils.logging import get_logger

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

def run_scraper():
    """
    Run the Forex Factory scraper.
    """
    logger.info("Starting Forex Factory scraper...")
    
    try:
        # Initialize scraper
        scraper = ForexFactoryScraper()
        
        # Scrape data
        events_data = scraper.scrape_calendar()
        
        if not events_data:
            logger.warning("No events found or failed to scrape.")
            return 1
        
        logger.info(f"Scraped {len(events_data)} events.")
        
        # Process data
        with get_db_session() as db:
            db_manager = ScraperDBManager(db)
            processed_count = db_manager.process_events(events_data)
            
        logger.info(f"Successfully processed {processed_count} events.")
        return 0
        
    except Exception as e:
        logger.error(f"Error running scraper: {str(e)}")
        return 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the Forex Factory scraper.")
    args = parser.parse_args()
    
    sys.exit(run_scraper()) 