"""
Script to run the sentiment analysis engine.
"""
import sys
import argparse
import traceback
from datetime import datetime, timedelta
from contextlib import contextmanager

from src.analysis.sentiment_engine import SentimentCalculator
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
def run_analysis(week_start: datetime = None, week_end: datetime = None):
    """
    Run the sentiment analysis.
    
    Args:
        week_start (datetime, optional): Start of the week to analyze.
        week_end (datetime, optional): End of the week to analyze.
        
    Returns:
        int: 0 for success, 1 for failure.
    """
    logger.info("Starting sentiment analysis...")
    success = False
    error_message = None
    currencies_analyzed = 0
    
    try:
        # Initialize sentiment calculator
        with get_db_session() as db:
            calculator = SentimentCalculator(db_session=db)
            
            # Calculate weekly sentiments
            sentiments = calculator.calculate_weekly_sentiments(week_start, week_end)
            
            if not sentiments:
                error_message = "No sentiment data calculated or no events found for the specified week."
                logger.warning(error_message)
                return 1
            
            currencies_analyzed = len(sentiments)
            success = True
            
            # Log results
            logger.info(f"Successfully analyzed {currencies_analyzed} currencies.")
            for currency, data in sentiments.items():
                resolution = data["resolution"]
                logger.info(f"{currency}: {resolution['final_sentiment']} ({resolution['reason']})")
        
        return 0
        
    except Exception as e:
        error_message = f"Error running sentiment analysis: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_message)
        return 1

def parse_date(date_str: str) -> datetime:
    """
    Parse a date string into a datetime object.
    
    Args:
        date_str (str): Date string in YYYY-MM-DD format.
        
    Returns:
        datetime: Parsed datetime object.
    """
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError(f"Invalid date format: {date_str}. Expected YYYY-MM-DD")

def run_analysis_cli():
    """
    CLI entry point for the sentiment analysis.
    """
    parser = argparse.ArgumentParser(description="Run the sentiment analysis engine.")
    parser.add_argument("--week-start", type=parse_date, help="Start date of the week to analyze (YYYY-MM-DD)")
    parser.add_argument("--week-end", type=parse_date, help="End date of the week to analyze (YYYY-MM-DD)")
    parser.add_argument("--current-week", action="store_true", help="Analyze the current week (default)")
    
    args = parser.parse_args()
    
    week_start = None
    week_end = None
    
    if args.week_start and args.week_end:
        week_start = args.week_start
        week_end = args.week_end
    elif args.week_start or args.week_end:
        parser.error("Both --week-start and --week-end must be provided together")
    
    sys.exit(run_analysis(week_start, week_end))

if __name__ == "__main__":
    run_analysis_cli() 