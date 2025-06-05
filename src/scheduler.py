"""
Scheduler for running the Forex Factory scraper and sentiment analysis at specified intervals.
"""
import os
import logging
import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from src.run_scraper import run_scraper
from src.run_analysis import run_analysis
from src.utils.logging import get_logger

# Load environment variables
load_dotenv()

# Get logger
logger = get_logger(__name__)

def get_scraper_schedule_time():
    """
    Get the schedule time for the scraper from environment variables.
    
    Returns:
        str: Schedule time in HH:MM format (default: 02:00)
    """
    schedule_time = os.getenv("SCRAPER_SCHEDULE_TIME", "02:00").split('#')[0].strip()
    return schedule_time

def get_analysis_schedule():
    """
    Get the schedule for sentiment analysis from environment variables.
    
    Returns:
        tuple: (day_of_week, time) where day_of_week is 0-6 (Monday=0) and time is HH:MM
    """
    schedule_day = os.getenv("ANALYSIS_SCHEDULE_DAY", "Monday").split('#')[0].strip()
    schedule_time = os.getenv("ANALYSIS_SCHEDULE_TIME", "06:00").split('#')[0].strip()
    
    # Convert day name to number (Monday=0, Sunday=6)
    day_mapping = {
        "monday": 0, "tuesday": 1, "wednesday": 2, "thursday": 3,
        "friday": 4, "saturday": 5, "sunday": 6
    }
    day_of_week = day_mapping.get(schedule_day.lower(), 0)  # Default to Monday
    
    return day_of_week, schedule_time

def get_actual_data_collection_config():
    """
    Get the configuration for actual data collection from environment variables.
    
    Returns:
        dict: Configuration dictionary with enabled status, interval, retry limit, and lookback days
    """
    config = {
        'enabled': os.getenv("ACTUAL_DATA_COLLECTION_ENABLED", "true").lower() == "true",
        'interval': int(os.getenv("ACTUAL_DATA_COLLECTION_INTERVAL", "4")),
        'retry_limit': int(os.getenv("ACTUAL_DATA_RETRY_LIMIT", "3")),
        'lookback_days': int(os.getenv("ACTUAL_DATA_LOOKBACK_DAYS", "7"))
    }
    return config

def run_weekly_analysis():
    """
    Wrapper function to run weekly sentiment analysis.
    This is called by the scheduler.
    """
    try:
        logger.info("Starting scheduled weekly sentiment analysis...")
        result = run_analysis()
        
        if result == 0:
            logger.info("Scheduled weekly sentiment analysis completed successfully")
        else:
            logger.error(f"Scheduled weekly sentiment analysis failed with exit code: {result}")
            
        return result
    except Exception as e:
        logger.error(f"Error in scheduled weekly sentiment analysis: {str(e)}")
        return 1

def run_actual_data_collection():
    """
    Wrapper function to run actual data collection.
    This is called by the scheduler.
    """
    try:
        from src.scraper.actual_data_collector import ActualDataCollector
        from src.analysis.sentiment_engine import SentimentCalculator
        
        config = get_actual_data_collection_config()
        
        logger.info("Starting scheduled actual data collection...")
        logger.info(f"Collection config: lookback_days={config['lookback_days']}, retry_limit={config['retry_limit']}")
        
        with ActualDataCollector(
            lookback_days=config['lookback_days'], 
            retry_limit=config['retry_limit']
        ) as collector:
            total_processed, successful_updates = collector.collect_all_missing_actual_data()
        
        if total_processed == 0:
            logger.info("No events missing actual data found")
            return 0
        
        success_rate = (successful_updates / total_processed) * 100 if total_processed > 0 else 0
        logger.info(f"Actual data collection completed: {successful_updates}/{total_processed} events updated ({success_rate:.1f}% success rate)")
        
        if successful_updates > 0:
            # Calculate actual sentiment for updated events
            logger.info("Calculating actual sentiment for updated events...")
            
            with SentimentCalculator() as calculator:
                actual_sentiments = calculator.calculate_actual_sentiment()
                logger.info(f"Calculated actual sentiment for {len(actual_sentiments)} currencies")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error in scheduled actual data collection: {str(e)}")
        return 1

def run_actual_data_health_check():
    """
    Phase 6: Wrapper function to check actual data collection health and send alerts.
    This is called by the scheduler.
    """
    try:
        from src.utils.alerting import check_and_send_alerts
        
        logger.info("Starting scheduled actual data health check...")
        check_and_send_alerts()
        logger.info("Actual data health check completed")
        return 0
        
    except Exception as e:
        logger.error(f"Error in scheduled actual data health check: {str(e)}")
        return 1

def schedule_scraper():
    """
    Schedule the scraper to run at the specified time.
    
    Returns:
        BackgroundScheduler: The scheduler instance
    """
    # Create scheduler
    scheduler = BackgroundScheduler()
    
    # Get schedule time for scraper
    schedule_time = get_scraper_schedule_time()
    hour, minute = schedule_time.split(":")
    
    # Schedule scraper to run daily at the specified time
    scheduler.add_job(
        run_scraper,
        trigger=CronTrigger(hour=int(hour), minute=int(minute)),
        id="forex_factory_scraper",
        name="Forex Factory Scraper",
        replace_existing=True
    )
    
    logger.info(f"Scheduled scraper to run daily at {schedule_time} UTC")
    
    # Get schedule for sentiment analysis
    analysis_day, analysis_time = get_analysis_schedule()
    analysis_hour, analysis_minute = analysis_time.split(":")
    
    # Schedule sentiment analysis to run weekly
    scheduler.add_job(
        run_weekly_analysis,
        trigger=CronTrigger(day_of_week=analysis_day, hour=int(analysis_hour), minute=int(analysis_minute)),
        id="weekly_sentiment_analysis",
        name="Weekly Sentiment Analysis",
        replace_existing=True
    )
    
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    logger.info(f"Scheduled sentiment analysis to run every {day_names[analysis_day]} at {analysis_time} UTC")
    
    # Get actual data collection configuration
    actual_config = get_actual_data_collection_config()
    
    if actual_config['enabled']:
        # Schedule actual data collection to run every X hours (default: every 4 hours)
        # Using cron expression: "0 */4 * * *" means every 4 hours at minute 0
        scheduler.add_job(
            run_actual_data_collection,
            trigger=CronTrigger(minute=0, hour=f"*/{actual_config['interval']}"),
            id="actual_data_collection",
            name="Actual Data Collection",
            replace_existing=True
        )
        
        logger.info(f"Scheduled actual data collection to run every {actual_config['interval']} hours")
        
        # Phase 6: Schedule health check for actual data collection
        # Run health check every 2 hours (more frequent than collection to catch issues quickly)
        health_check_interval = max(1, actual_config['interval'] // 2)  # Half the collection interval, minimum 1 hour
        scheduler.add_job(
            run_actual_data_health_check,
            trigger=CronTrigger(minute=30, hour=f"*/{health_check_interval}"),  # Offset by 30 minutes from collection
            id="actual_data_health_check",
            name="Actual Data Health Check",
            replace_existing=True
        )
        
        logger.info(f"Scheduled actual data health check to run every {health_check_interval} hours")
    else:
        logger.info("Actual data collection is disabled via configuration")
    
    return scheduler

def start_scheduler():
    """
    Start the scheduler.
    """
    scheduler = schedule_scraper()
    
    try:
        scheduler.start()
        logger.info("Scheduler started with both scraper and sentiment analysis jobs")
        
        # Log scheduled jobs
        jobs = scheduler.get_jobs()
        logger.info(f"Active jobs: {len(jobs)}")
        for job in jobs:
            logger.info(f"  - {job.name} (ID: {job.id})")
        
        # Keep the main thread running
        while True:
            time.sleep(60)
            
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")
        scheduler.shutdown()

if __name__ == "__main__":
    start_scheduler() 