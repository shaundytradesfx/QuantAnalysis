"""
Main script for the Forex Factory Sentiment Analyzer.
"""
import os
import sys
import argparse
import logging
import time
import signal
from datetime import datetime
from dotenv import load_dotenv

from src.scheduler import schedule_scraper, start_scheduler
from src.run_scraper import run_scraper
from src.run_analysis import run_analysis, parse_date
from src.health_check import run_health_check
from src.utils.logging import get_logger

# Load environment variables
load_dotenv()

# Get logger
logger = get_logger(__name__)

def parse_args():
    """
    Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Forex Factory Sentiment Analyzer")
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Scraper command
    scraper_parser = subparsers.add_parser("scrape", help="Run the scraper once")
    scraper_parser.add_argument("--force", action="store_true", help="Force scraper to run regardless of schedule")
    
    # Analysis command
    analysis_parser = subparsers.add_parser("analyze", help="Run sentiment analysis")
    analysis_parser.add_argument("--week-start", type=parse_date, help="Start date of the week to analyze (YYYY-MM-DD)")
    analysis_parser.add_argument("--week-end", type=parse_date, help="End date of the week to analyze (YYYY-MM-DD)")
    analysis_parser.add_argument("--current-week", action="store_true", help="Analyze the current week (default)")
    
    # Discord notification command
    notify_parser = subparsers.add_parser("notify", help="Send Discord notification")
    notify_parser.add_argument("--week-start", type=parse_date, help="Start date of the week to notify about (YYYY-MM-DD)")
    notify_parser.add_argument("--week-end", type=parse_date, help="End date of the week to notify about (YYYY-MM-DD)")
    notify_parser.add_argument("--current-week", action="store_true", help="Notify about the current week (default)")
    notify_parser.add_argument("--test", action="store_true", help="Test Discord webhook connections")
    
    # Scheduler command
    scheduler_parser = subparsers.add_parser("schedule", help="Run the scraper on a schedule")
    
    # Health check command
    health_parser = subparsers.add_parser("health", help="Run health check")
    
    return parser.parse_args()

def run_discord_notification(week_start=None, week_end=None, test_mode=False):
    """
    Run Discord notification.
    
    Args:
        week_start (datetime, optional): Start of week to notify about
        week_end (datetime, optional): End of week to notify about
        test_mode (bool): Whether to run in test mode
        
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    try:
        from src.discord import DiscordNotifier
        from src.analysis.sentiment_engine import SentimentCalculator
        
        # Initialize Discord notifier
        notifier = DiscordNotifier()
        
        if test_mode:
            logger.info("Testing Discord webhook connections...")
            results = notifier.test_connection()
            
            for webhook_type, success in results.items():
                status = "✅ PASSED" if success else "❌ FAILED"
                logger.info(f"{webhook_type}: {status}")
            
            if all(results.values()):
                logger.info("All Discord webhook tests passed!")
                return 0
            else:
                logger.error("Some Discord webhook tests failed!")
                return 1
        
        # Get sentiment data for the specified week
        with SentimentCalculator() as calculator:
            if week_start and week_end:
                sentiments = calculator.calculate_weekly_sentiments(week_start, week_end)
                notification_week_start = week_start
            else:
                sentiments = calculator.calculate_weekly_sentiments()
                notification_week_start, _ = calculator.get_current_week_bounds()
        
        if not sentiments:
            logger.warning("No sentiment data found for the specified week")
            # Send empty report notification
            success = notifier.send_weekly_report({}, notification_week_start)
        else:
            logger.info(f"Sending Discord notification for {len(sentiments)} currencies")
            success = notifier.send_weekly_report(sentiments, notification_week_start)
        
        if success:
            logger.info("Discord notification sent successfully!")
            return 0
        else:
            logger.error("Failed to send Discord notification")
            return 1
            
    except Exception as e:
        logger.error(f"Error running Discord notification: {str(e)}")
        return 1

def handle_signal(signum, frame):
    """
    Handle signals (e.g., SIGINT, SIGTERM).
    
    Args:
        signum: Signal number.
        frame: Current stack frame.
    """
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)

def main():
    """
    Main entry point for the application.
    
    Returns:
        int: Exit code (0 for success, non-zero for failure).
    """
    # Register signal handlers
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    
    # Parse arguments
    args = parse_args()
    
    # Run command
    if args.command == "scrape":
        logger.info("Running scraper...")
        return run_scraper()
    elif args.command == "analyze":
        logger.info("Running sentiment analysis...")
        week_start = None
        week_end = None
        
        if args.week_start and args.week_end:
            week_start = args.week_start
            week_end = args.week_end
        elif args.week_start or args.week_end:
            logger.error("Both --week-start and --week-end must be provided together")
            return 1
            
        return run_analysis(week_start, week_end)
    elif args.command == "notify":
        logger.info("Running Discord notification...")
        week_start = None
        week_end = None
        
        if args.week_start and args.week_end:
            week_start = args.week_start
            week_end = args.week_end
        elif args.week_start or args.week_end:
            logger.error("Both --week-start and --week-end must be provided together")
            return 1
            
        return run_discord_notification(week_start, week_end, args.test)
    elif args.command == "schedule":
        logger.info("Starting scheduler...")
        start_scheduler()
        return 0
    elif args.command == "health":
        logger.info("Running health check...")
        return run_health_check()
    else:
        logger.error(f"Unknown command: {args.command}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 