"""
Scheduler for running the Forex Factory scraper at specified intervals.
"""
import os
import logging
import time
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from src.run_scraper import run_scraper
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
    schedule_time = os.getenv("SCRAPER_SCHEDULE_TIME", "02:00")
    return schedule_time

def schedule_scraper():
    """
    Schedule the scraper to run at the specified time.
    
    Returns:
        BackgroundScheduler: The scheduler instance
    """
    # Create scheduler
    scheduler = BackgroundScheduler()
    
    # Get schedule time
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
    
    return scheduler

def start_scheduler():
    """
    Start the scheduler.
    """
    scheduler = schedule_scraper()
    
    try:
        scheduler.start()
        logger.info("Scheduler started")
        
        # Keep the main thread running
        while True:
            time.sleep(60)
            
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped")
        scheduler.shutdown()

if __name__ == "__main__":
    start_scheduler() 