"""
Health check module for monitoring the scraper's health and sending alerts.
"""
import os
import sys
import argparse
from datetime import datetime, timedelta
import requests
from dotenv import load_dotenv

from src.utils.logging import get_logger
from src.utils.monitoring import get_last_successful_run, check_scraper_health

# Load environment variables
load_dotenv()

logger = get_logger(__name__)

def send_health_alert(message):
    """
    Send a health alert to the Discord webhook.
    
    Args:
        message (str): The alert message to send.
        
    Returns:
        bool: True if the alert was sent successfully, False otherwise.
    """
    # Get Discord health webhook URL from environment variables
    webhook_url = os.getenv("DISCORD_HEALTH_WEBHOOK_URL")
    
    if not webhook_url:
        logger.error("DISCORD_HEALTH_WEBHOOK_URL environment variable not set")
        return False
    
    # Prepare payload
    payload = {
        "content": f"⚠️ **HEALTH ALERT** ⚠️\n\n{message}\n\n_Timestamp: {datetime.utcnow().isoformat()}_"
    }
    
    try:
        # Send webhook
        response = requests.post(webhook_url, json=payload, timeout=10)
        
        if response.status_code >= 200 and response.status_code < 300:
            logger.info(f"Health alert sent successfully: {message}")
            return True
        else:
            logger.error(f"Failed to send health alert: {response.status_code} {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending health alert: {str(e)}")
        return False

def check_health():
    """
    Check the health of the scraper and send alerts if needed.
    
    Returns:
        bool: True if the scraper is healthy, False otherwise.
    """
    logger.info("Running health check...")
    
    # Check scraper health
    is_healthy = check_scraper_health()
    
    if not is_healthy:
        # Get last successful run
        last_success = get_last_successful_run()
        
        if last_success:
            last_success_time = datetime.fromisoformat(last_success)
            time_diff = datetime.utcnow() - last_success_time
            hours = int(time_diff.total_seconds() / 3600)
            
            message = f"Scraper health check failed. Last successful run was {hours} hours ago at {last_success}."
        else:
            message = "Scraper health check failed. No successful runs found."
            
        # Send alert
        send_health_alert(message)
        
        logger.warning(message)
        return False
    
    logger.info("Health check passed. Scraper is healthy.")
    return True

def run_health_check():
    """
    Run the health check and return the exit code.
    
    Returns:
        int: 0 if the scraper is healthy, 1 otherwise.
    """
    try:
        is_healthy = check_health()
        return 0 if is_healthy else 1
    except Exception as e:
        logger.error(f"Error running health check: {str(e)}")
        return 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run health check for the Forex Factory scraper.")
    args = parser.parse_args()
    
    sys.exit(run_health_check()) 