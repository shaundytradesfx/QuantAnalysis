"""
Alerting system for actual data collection monitoring.
Phase 6: Enhanced error handling and alerting for actual data functionality.
"""
import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from src.utils.logging import get_logger
from src.utils.actual_data_monitoring import ActualDataMonitor
from src.database.config import SessionLocal
from src.database.models import Config

logger = get_logger(__name__)

class ActualDataAlerter:
    """
    Alerting system for actual data collection issues.
    """
    
    def __init__(self, 
                 health_webhook_url: Optional[str] = None,
                 db_session: Optional[Session] = None):
        """
        Initialize the alerter.
        
        Args:
            health_webhook_url (str, optional): Discord webhook URL for health alerts.
            db_session (Session, optional): Database session. If None, creates a new one.
        """
        self.health_webhook_url = health_webhook_url or os.getenv("DISCORD_HEALTH_WEBHOOK_URL")
        self.db = db_session
        self.close_db_on_exit = db_session is None
        
        if self.db is None:
            self.db = SessionLocal()
            
        # Alert configuration
        self.alert_cooldown_hours = int(os.getenv("ALERT_COOLDOWN_HOURS", "4"))  # Don't spam alerts
        self.enable_discord_alerts = os.getenv("ENABLE_DISCORD_ALERTS", "true").lower() == "true"
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.close_db_on_exit and self.db:
            self.db.close()
    
    def check_and_send_alerts(self) -> None:
        """
        Check for alert conditions and send notifications if needed.
        """
        try:
            with ActualDataMonitor(db_session=self.db) as monitor:
                health_status = monitor.get_collection_health_status()
                accuracy_stats = monitor.get_accuracy_statistics()
                
                # Check for collection health issues
                if health_status["status"] in ["warning", "critical"]:
                    self._send_health_alert(health_status, accuracy_stats)
                
                # Check for accuracy issues
                if accuracy_stats["total_comparisons"] > 10:  # Only alert if we have enough data
                    if accuracy_stats["overall_accuracy"] < 40:  # Less than 40% accuracy
                        self._send_accuracy_alert(accuracy_stats)
                
                # Check for prolonged collection failures
                self._check_prolonged_failures(health_status)
                
        except Exception as e:
            logger.error(f"Error checking alerts: {str(e)}")
    
    def _send_health_alert(self, health_status: Dict[str, Any], accuracy_stats: Dict[str, Any]) -> None:
        """
        Send a health alert about actual data collection issues.
        
        Args:
            health_status (Dict[str, Any]): Collection health status.
            accuracy_stats (Dict[str, Any]): Accuracy statistics.
        """
        try:
            # Check if we should send an alert (cooldown logic)
            if not self._should_send_alert("health", health_status["status"]):
                return
            
            # Determine alert emoji and color
            if health_status["status"] == "critical":
                emoji = "🚨"
                color = 15158332  # Red
            elif health_status["status"] == "warning":
                emoji = "⚠️"
                color = 16776960  # Yellow
            else:
                emoji = "ℹ️"
                color = 3447003  # Blue
            
            # Build alert message
            embed = {
                "title": f"{emoji} Actual Data Collection Alert",
                "description": health_status["message"],
                "color": color,
                "timestamp": datetime.utcnow().isoformat(),
                "fields": [
                    {
                        "name": "Success Rate",
                        "value": f"{health_status['success_rate']:.1f}%",
                        "inline": True
                    },
                    {
                        "name": "Last Run",
                        "value": health_status.get("last_run", "Unknown"),
                        "inline": True
                    },
                    {
                        "name": "Hours Since Last Run",
                        "value": f"{health_status.get('time_since_last_run_hours', 0):.1f}",
                        "inline": True
                    }
                ]
            }
            
            # Add accuracy information if available
            if accuracy_stats["total_comparisons"] > 0:
                embed["fields"].append({
                    "name": "Forecast Accuracy",
                    "value": f"{accuracy_stats['overall_accuracy']:.1f}%",
                    "inline": True
                })
            
            # Add last run details if available
            if "last_run_details" in health_status and health_status["last_run_details"]:
                details = health_status["last_run_details"]
                embed["fields"].append({
                    "name": "Last Run Details",
                    "value": f"Processed: {details.get('events_processed', 0)}, Updated: {details.get('events_updated', 0)}, Time: {details.get('execution_time', 0):.1f}s",
                    "inline": False
                })
            
            payload = {
                "embeds": [embed]
            }
            
            self._send_discord_notification(payload, "health alert")
            self._record_alert_sent("health", health_status["status"])
            
        except Exception as e:
            logger.error(f"Error sending health alert: {str(e)}")
    
    def _send_accuracy_alert(self, accuracy_stats: Dict[str, Any]) -> None:
        """
        Send an alert about low forecast accuracy.
        
        Args:
            accuracy_stats (Dict[str, Any]): Accuracy statistics.
        """
        try:
            # Check if we should send an alert (cooldown logic)
            if not self._should_send_alert("accuracy", "warning"):
                return
            
            # Build accuracy alert
            embed = {
                "title": "📊 Low Forecast Accuracy Alert",
                "description": f"Forecast accuracy has dropped to {accuracy_stats['overall_accuracy']:.1f}%",
                "color": 16776960,  # Yellow
                "timestamp": datetime.utcnow().isoformat(),
                "fields": [
                    {
                        "name": "Overall Accuracy",
                        "value": f"{accuracy_stats['overall_accuracy']:.1f}%",
                        "inline": True
                    },
                    {
                        "name": "Total Comparisons",
                        "value": str(accuracy_stats['total_comparisons']),
                        "inline": True
                    },
                    {
                        "name": "Period",
                        "value": f"Last {accuracy_stats['period_days']} days",
                        "inline": True
                    }
                ]
            }
            
            # Add currency breakdown
            currency_breakdown = []
            for currency, stats in accuracy_stats.get("currency_breakdown", {}).items():
                if stats["total_comparisons"] >= 3:  # Only show currencies with enough data
                    currency_breakdown.append(f"{currency}: {stats['accuracy']:.1f}% ({stats['accurate_predictions']}/{stats['total_comparisons']})")
            
            if currency_breakdown:
                embed["fields"].append({
                    "name": "Currency Breakdown",
                    "value": "\n".join(currency_breakdown[:8]),  # Limit to 8 currencies
                    "inline": False
                })
            
            payload = {
                "embeds": [embed]
            }
            
            self._send_discord_notification(payload, "accuracy alert")
            self._record_alert_sent("accuracy", "warning")
            
        except Exception as e:
            logger.error(f"Error sending accuracy alert: {str(e)}")
    
    def _check_prolonged_failures(self, health_status: Dict[str, Any]) -> None:
        """
        Check for prolonged collection failures and send alert if needed.
        
        Args:
            health_status (Dict[str, Any]): Collection health status.
        """
        try:
            # Check if there have been no successful runs in the last 24 hours
            hours_since_last = health_status.get("time_since_last_run_hours", 0)
            
            if hours_since_last > 24:  # More than 24 hours
                if self._should_send_alert("prolonged_failure", "critical"):
                    embed = {
                        "title": "🚨 Prolonged Collection Failure",
                        "description": f"No actual data collection attempts in the last {hours_since_last:.1f} hours",
                        "color": 15158332,  # Red
                        "timestamp": datetime.utcnow().isoformat(),
                        "fields": [
                            {
                                "name": "Hours Without Collection",
                                "value": f"{hours_since_last:.1f}",
                                "inline": True
                            },
                            {
                                "name": "Expected Interval",
                                "value": "Every 4 hours",
                                "inline": True
                            },
                            {
                                "name": "Action Required",
                                "value": "Check scheduler and application health",
                                "inline": False
                            }
                        ]
                    }
                    
                    payload = {
                        "embeds": [embed]
                    }
                    
                    self._send_discord_notification(payload, "prolonged failure alert")
                    self._record_alert_sent("prolonged_failure", "critical")
            
        except Exception as e:
            logger.error(f"Error checking prolonged failures: {str(e)}")
    
    def _should_send_alert(self, alert_type: str, severity: str) -> bool:
        """
        Check if an alert should be sent based on cooldown logic.
        
        Args:
            alert_type (str): Type of alert (health, accuracy, prolonged_failure).
            severity (str): Severity level (info, warning, critical).
            
        Returns:
            bool: True if alert should be sent.
        """
        try:
            if not self.enable_discord_alerts:
                return False
            
            # Get last alert time for this type
            config = self.db.query(Config).filter(Config.key == f"LAST_ALERT_{alert_type.upper()}").first()
            
            if not config:
                return True  # No previous alert, send it
            
            last_alert_time = datetime.fromisoformat(config.value)
            current_time = datetime.utcnow()
            time_diff = current_time - last_alert_time
            
            # Check cooldown period
            cooldown_hours = self.alert_cooldown_hours
            
            # Reduce cooldown for critical alerts
            if severity == "critical":
                cooldown_hours = max(1, cooldown_hours // 2)
            
            return time_diff.total_seconds() > (cooldown_hours * 3600)
            
        except Exception as e:
            logger.error(f"Error checking alert cooldown: {str(e)}")
            return True  # Send alert if there's an error checking
    
    def _record_alert_sent(self, alert_type: str, severity: str) -> None:
        """
        Record that an alert was sent for cooldown tracking.
        
        Args:
            alert_type (str): Type of alert sent.
            severity (str): Severity level.
        """
        try:
            current_time = datetime.utcnow().isoformat()
            
            # Update last alert time
            config = self.db.query(Config).filter(Config.key == f"LAST_ALERT_{alert_type.upper()}").first()
            
            if config:
                config.value = current_time
            else:
                config = Config(
                    key=f"LAST_ALERT_{alert_type.upper()}",
                    value=current_time
                )
                self.db.add(config)
            
            self.db.commit()
            
            logger.info(f"Recorded alert sent: {alert_type} ({severity})")
            
        except Exception as e:
            logger.error(f"Error recording alert sent: {str(e)}")
    
    def _send_discord_notification(self, payload: Dict[str, Any], alert_type: str) -> bool:
        """
        Send a Discord notification.
        
        Args:
            payload (Dict[str, Any]): Discord webhook payload.
            alert_type (str): Type of alert for logging.
            
        Returns:
            bool: True if notification sent successfully.
        """
        try:
            if not self.health_webhook_url:
                logger.warning(f"No health webhook URL configured, cannot send {alert_type}")
                return False
            
            response = requests.post(
                self.health_webhook_url,
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"Successfully sent {alert_type} to Discord")
                return True
            else:
                logger.error(f"Failed to send {alert_type} to Discord: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending Discord notification for {alert_type}: {str(e)}")
            return False
    
    def send_test_alert(self) -> bool:
        """
        Send a test alert to verify Discord integration.
        
        Returns:
            bool: True if test alert sent successfully.
        """
        try:
            embed = {
                "title": "🧪 Actual Data Monitoring Test",
                "description": "This is a test alert to verify actual data monitoring is working correctly.",
                "color": 3447003,  # Blue
                "timestamp": datetime.utcnow().isoformat(),
                "fields": [
                    {
                        "name": "Status",
                        "value": "Test Alert",
                        "inline": True
                    },
                    {
                        "name": "Time",
                        "value": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC"),
                        "inline": True
                    }
                ]
            }
            
            payload = {
                "embeds": [embed]
            }
            
            return self._send_discord_notification(payload, "test alert")
            
        except Exception as e:
            logger.error(f"Error sending test alert: {str(e)}")
            return False

def check_and_send_alerts() -> None:
    """
    Convenience function to check and send alerts.
    """
    try:
        with ActualDataAlerter() as alerter:
            alerter.check_and_send_alerts()
    except Exception as e:
        logger.error(f"Error in check_and_send_alerts: {str(e)}")

def send_test_alert() -> bool:
    """
    Convenience function to send a test alert.
    
    Returns:
        bool: True if test alert sent successfully.
    """
    try:
        with ActualDataAlerter() as alerter:
            return alerter.send_test_alert()
    except Exception as e:
        logger.error(f"Error in send_test_alert: {str(e)}")
        return False 