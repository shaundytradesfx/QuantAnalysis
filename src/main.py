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
    
    # Actual data collection command
    actual_parser = subparsers.add_parser("collect-actual", help="Collect actual data for past events")
    actual_parser.add_argument("--lookback-days", type=int, default=7, help="How many days back to look for missing actual data (default: 7)")
    actual_parser.add_argument("--retry-limit", type=int, default=3, help="Maximum retries for missing actual data (default: 3)")
    
    # Phase 6: Monitoring and alerting commands
    monitor_parser = subparsers.add_parser("monitor", help="Monitoring and alerting commands")
    monitor_subparsers = monitor_parser.add_subparsers(dest="monitor_command", help="Monitor sub-commands")
    
    # Health check command
    health_parser = monitor_subparsers.add_parser("health", help="Check actual data collection health")
    
    # Test alert command
    test_alert_parser = monitor_subparsers.add_parser("test-alert", help="Send a test alert to Discord")
    
    # Monitoring stats command
    stats_parser = monitor_subparsers.add_parser("stats", help="Show monitoring statistics")
    stats_parser.add_argument("--days", type=int, default=30, help="Number of days to look back for accuracy stats (default: 30)")
    
    # Check alerts command
    check_alerts_parser = monitor_subparsers.add_parser("check-alerts", help="Check and send alerts if needed")
    
    # Discord notification command
    notify_parser = subparsers.add_parser("notify", help="Send Discord notification")
    notify_parser.add_argument("--week-start", type=parse_date, help="Start date of the week to notify about (YYYY-MM-DD)")
    notify_parser.add_argument("--week-end", type=parse_date, help="End date of the week to notify about (YYYY-MM-DD)")
    notify_parser.add_argument("--current-week", action="store_true", help="Notify about the current week (default)")
    notify_parser.add_argument("--test", action="store_true", help="Test Discord webhook connections")
    
    # Scheduler command
    scheduler_parser = subparsers.add_parser("schedule", help="Run the scraper on a schedule")
    
    # Web server command
    web_parser = subparsers.add_parser("web", help="Start the web dashboard server")
    web_parser.add_argument("--host", default="127.0.0.1", help="Host to bind the server to (default: 127.0.0.1)")
    web_parser.add_argument("--port", type=int, default=8000, help="Port to bind the server to (default: 8000)")
    web_parser.add_argument("--no-reload", action="store_true", help="Disable auto-reload in development")
    
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
                notification_week_start, _ = calculator.get_next_week_bounds()
        
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

def run_web_server(host="127.0.0.1", port=8000, reload=True):
    """
    Run the web dashboard server.
    
    Args:
        host (str): Host to bind the server to
        port (int): Port to bind the server to
        reload (bool): Whether to enable auto-reload
        
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    # Ensure logger is available in this scope
    from src.utils.logging import get_logger
    local_logger = get_logger(__name__)
    
    try:
        from src.api.server import run_server
        local_logger.info(f"Starting web dashboard server on {host}:{port}")
        run_server(host=host, port=port, reload=reload)
        return 0
    except Exception as e:
        local_logger.error(f"Error starting web server: {str(e)}")
        return 1

def run_actual_data_collection(lookback_days=7, retry_limit=3):
    """
    Run actual data collection for past events.
    
    Args:
        lookback_days (int): How many days back to look for missing actual data
        retry_limit (int): Maximum retries for missing actual data
        
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    try:
        from src.scraper.actual_data_collector import ActualDataCollector
        
        logger.info(f"Starting actual data collection (lookback: {lookback_days} days, retry limit: {retry_limit})")
        
        with ActualDataCollector(lookback_days=lookback_days, retry_limit=retry_limit) as collector:
            total_processed, successful_updates = collector.collect_all_missing_actual_data()
        
        if total_processed == 0:
            logger.info("No events missing actual data found")
            return 0
        
        success_rate = (successful_updates / total_processed) * 100 if total_processed > 0 else 0
        logger.info(f"Actual data collection completed: {successful_updates}/{total_processed} events updated ({success_rate:.1f}% success rate)")
        
        if successful_updates > 0:
            # Calculate actual sentiment for updated events
            logger.info("Calculating actual sentiment for updated events...")
            from src.analysis.sentiment_engine import SentimentCalculator
            
            with SentimentCalculator() as calculator:
                actual_sentiments = calculator.calculate_actual_sentiment()
                logger.info(f"Calculated actual sentiment for {len(actual_sentiments)} currencies")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error running actual data collection: {str(e)}")
        return 1

def run_monitoring_health_check():
    """
    Phase 6: Run health check for actual data collection.
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    try:
        from src.utils.actual_data_monitoring import ActualDataMonitor
        
        logger.info("Running actual data collection health check...")
        
        with ActualDataMonitor() as monitor:
            health_status = monitor.get_collection_health_status()
            
        print(f"\n📊 Actual Data Collection Health Status")
        print(f"Status: {health_status['status'].upper()}")
        print(f"Message: {health_status['message']}")
        print(f"Success Rate: {health_status['success_rate']:.1f}%")
        print(f"Last Run: {health_status.get('last_run', 'Unknown')}")
        print(f"Hours Since Last Run: {health_status.get('time_since_last_run_hours', 0):.1f}")
        
        if health_status['status'] == 'critical':
            return 2  # Critical status
        elif health_status['status'] == 'warning':
            return 1  # Warning status
        else:
            return 0  # Healthy status
        
    except Exception as e:
        logger.error(f"Error running health check: {str(e)}")
        return 1

def run_test_alert():
    """
    Phase 6: Send a test alert to Discord.
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    try:
        from src.utils.alerting import send_test_alert
        
        logger.info("Sending test alert to Discord...")
        
        success = send_test_alert()
        
        if success:
            print("✅ Test alert sent successfully to Discord")
            return 0
        else:
            print("❌ Failed to send test alert to Discord")
            return 1
        
    except Exception as e:
        logger.error(f"Error sending test alert: {str(e)}")
        return 1

def run_monitoring_stats(days_back=30):
    """
    Phase 6: Show monitoring statistics.
    
    Args:
        days_back (int): Number of days to look back for accuracy stats
        
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    try:
        from src.utils.actual_data_monitoring import get_monitoring_stats
        
        logger.info(f"Getting monitoring statistics for the last {days_back} days...")
        
        stats = get_monitoring_stats()
        
        print(f"\n📈 Actual Data Monitoring Statistics")
        print(f"Last Updated: {stats['last_updated']}")
        
        # Collection Health
        health = stats['collection_health']
        print(f"\n🏥 Collection Health:")
        print(f"  Status: {health['status'].upper()}")
        print(f"  Message: {health['message']}")
        print(f"  Success Rate: {health['success_rate']:.1f}%")
        print(f"  Last Run: {health.get('last_run', 'Unknown')}")
        
        # Accuracy Statistics
        accuracy = stats['accuracy_statistics']
        print(f"\n🎯 Forecast Accuracy (Last {accuracy['period_days']} days):")
        print(f"  Overall Accuracy: {accuracy['overall_accuracy']:.1f}%")
        print(f"  Total Comparisons: {accuracy['total_comparisons']}")
        print(f"  Accurate Predictions: {accuracy['accurate_predictions']}")
        
        if accuracy.get('currency_breakdown'):
            print(f"\n💱 Currency Breakdown:")
            for currency, stats in accuracy['currency_breakdown'].items():
                print(f"  {currency}: {stats['accuracy']:.1f}% ({stats['accurate_predictions']}/{stats['total_comparisons']})")
        
        return 0
        
    except Exception as e:
        logger.error(f"Error getting monitoring stats: {str(e)}")
        return 1

def run_check_alerts():
    """
    Phase 6: Check and send alerts if needed.
    
    Returns:
        int: Exit code (0 for success, non-zero for failure)
    """
    try:
        from src.utils.alerting import check_and_send_alerts
        
        logger.info("Checking for alert conditions...")
        
        check_and_send_alerts()
        
        print("✅ Alert check completed")
        return 0
        
    except Exception as e:
        logger.error(f"Error checking alerts: {str(e)}")
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
        return run_scraper(force=args.force)
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
    elif args.command == "web":
        logger.info("Starting web dashboard server...")
        reload = not args.no_reload
        return run_web_server(args.host, args.port, reload)
    elif args.command == "collect-actual":
        logger.info("Running actual data collection...")
        return run_actual_data_collection(args.lookback_days, args.retry_limit)
    elif args.command == "monitor":
        if args.monitor_command == "health":
            logger.info("Running monitoring health check...")
            return run_monitoring_health_check()
        elif args.monitor_command == "test-alert":
            logger.info("Sending test alert...")
            return run_test_alert()
        elif args.monitor_command == "stats":
            logger.info("Getting monitoring statistics...")
            return run_monitoring_stats(args.days)
        elif args.monitor_command == "check-alerts":
            logger.info("Checking alerts...")
            return run_check_alerts()
        else:
            logger.error(f"Unknown monitor command: {args.monitor_command}")
            return 1
    else:
        logger.error(f"Unknown command: {args.command}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 