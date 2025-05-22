"""
Main script for the Forex Factory Sentiment Analyzer.
"""
import os
import sys
import argparse
import logging
import time
import signal
from dotenv import load_dotenv

from src.scheduler import schedule_scraper, start_scheduler
from src.run_scraper import run_scraper
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
    
    # Scheduler command
    scheduler_parser = subparsers.add_parser("schedule", help="Run the scraper on a schedule")
    
    # Health check command
    health_parser = subparsers.add_parser("health", help="Run health check")
    
    return parser.parse_args()

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