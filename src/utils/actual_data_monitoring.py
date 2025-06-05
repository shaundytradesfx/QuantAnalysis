"""
Monitoring utilities for actual data collection functionality.
Phase 6: Comprehensive monitoring and error handling for actual data.
"""
import os
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from sqlalchemy.orm import Session

from src.utils.logging import get_logger
from src.database.config import SessionLocal
from src.database.models import Config

logger = get_logger(__name__)

class ActualDataMonitor:
    """
    Monitor for actual data collection operations and health.
    """
    
    def __init__(self, db_session: Optional[Session] = None):
        """
        Initialize the actual data monitor.
        
        Args:
            db_session (Session, optional): Database session. If None, creates a new one.
        """
        self.db = db_session
        self.close_db_on_exit = db_session is None
        
        if self.db is None:
            self.db = SessionLocal()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.close_db_on_exit and self.db:
            self.db.close()
    
    def track_collection_attempt(self, 
                                events_processed: int, 
                                events_updated: int, 
                                success: bool, 
                                execution_time: float,
                                error_message: Optional[str] = None) -> None:
        """
        Track an actual data collection attempt.
        
        Args:
            events_processed (int): Number of events processed.
            events_updated (int): Number of events successfully updated.
            success (bool): Whether the collection was successful.
            execution_time (float): Time taken to execute in seconds.
            error_message (str, optional): Error message if failed.
        """
        try:
            timestamp = datetime.utcnow().isoformat()
            success_rate = (events_updated / events_processed * 100) if events_processed > 0 else 0
            
            collection_data = {
                "timestamp": timestamp,
                "events_processed": events_processed,
                "events_updated": events_updated,
                "success": success,
                "success_rate": success_rate,
                "execution_time": execution_time,
                "error_message": error_message
            }
            
            # Get existing collection history or create new
            config = self.db.query(Config).filter(Config.key == "ACTUAL_DATA_COLLECTION_HISTORY").first()
            
            if config:
                # Parse existing history
                history = json.loads(config.value)
                # Add new collection attempt
                history.append(collection_data)
                # Keep only last 50 attempts
                if len(history) > 50:
                    history = history[-50:]
                # Update config
                config.value = json.dumps(history)
            else:
                # Create new history
                config = Config(
                    key="ACTUAL_DATA_COLLECTION_HISTORY",
                    value=json.dumps([collection_data])
                )
                self.db.add(config)
            
            self.db.commit()
            
            logger.info(f"Tracked actual data collection: {collection_data}")
            
            # Check for alerting conditions
            self._check_failure_patterns()
            
        except Exception as e:
            logger.error(f"Failed to track actual data collection attempt: {str(e)}")
    
    def track_accuracy_metrics(self, 
                              currency: str, 
                              forecast_sentiment: int, 
                              actual_sentiment: int,
                              event_name: str,
                              forecast_value: Optional[float] = None,
                              actual_value: Optional[float] = None) -> None:
        """
        Track forecast vs actual accuracy metrics.
        
        Args:
            currency (str): Currency code.
            forecast_sentiment (int): Forecast sentiment (-1, 0, 1).
            actual_sentiment (int): Actual sentiment (-1, 0, 1).
            event_name (str): Name of the economic event.
            forecast_value (float, optional): Forecast value.
            actual_value (float, optional): Actual value.
        """
        try:
            timestamp = datetime.utcnow().isoformat()
            accuracy_match = forecast_sentiment == actual_sentiment
            
            accuracy_data = {
                "timestamp": timestamp,
                "currency": currency,
                "event_name": event_name,
                "forecast_sentiment": forecast_sentiment,
                "actual_sentiment": actual_sentiment,
                "accuracy_match": accuracy_match,
                "forecast_value": forecast_value,
                "actual_value": actual_value
            }
            
            # Get existing accuracy history or create new
            config = self.db.query(Config).filter(Config.key == "FORECAST_ACCURACY_HISTORY").first()
            
            if config:
                # Parse existing history
                history = json.loads(config.value)
                # Add new accuracy data
                history.append(accuracy_data)
                # Keep only last 200 accuracy records
                if len(history) > 200:
                    history = history[-200:]
                # Update config
                config.value = json.dumps(history)
            else:
                # Create new history
                config = Config(
                    key="FORECAST_ACCURACY_HISTORY",
                    value=json.dumps([accuracy_data])
                )
                self.db.add(config)
            
            self.db.commit()
            
            # Log accuracy result
            match_str = "✅ MATCH" if accuracy_match else "❌ MISMATCH"
            logger.info(f"Accuracy tracking - {currency} {event_name}: Forecast={forecast_sentiment}, Actual={actual_sentiment} - {match_str}")
            
        except Exception as e:
            logger.error(f"Failed to track accuracy metrics: {str(e)}")
    
    def get_collection_health_status(self) -> Dict[str, Any]:
        """
        Get the current health status of actual data collection.
        
        Returns:
            Dict[str, Any]: Health status information.
        """
        try:
            config = self.db.query(Config).filter(Config.key == "ACTUAL_DATA_COLLECTION_HISTORY").first()
            
            if not config:
                return {
                    "status": "unknown",
                    "message": "No collection history found",
                    "last_run": None,
                    "success_rate": 0
                }
            
            history = json.loads(config.value)
            
            if not history:
                return {
                    "status": "unknown",
                    "message": "Empty collection history",
                    "last_run": None,
                    "success_rate": 0
                }
            
            # Get last run info
            last_run = history[-1]
            last_run_time = datetime.fromisoformat(last_run["timestamp"])
            current_time = datetime.utcnow()
            time_since_last = current_time - last_run_time
            
            # Calculate success rate for last 10 runs
            recent_runs = history[-10:]
            successful_runs = sum(1 for run in recent_runs if run.get("success", False))
            success_rate = (successful_runs / len(recent_runs)) * 100
            
            # Determine health status
            status = "healthy"
            message = "Actual data collection is operating normally"
            
            # Check for concerning patterns
            if time_since_last.total_seconds() > 8 * 60 * 60:  # More than 8 hours since last run
                status = "warning"
                message = "No recent actual data collection attempts"
            elif success_rate < 50:
                status = "critical"
                message = f"Low success rate: {success_rate:.1f}%"
            elif not last_run.get("success", False):
                status = "warning"
                message = "Last collection attempt failed"
            
            return {
                "status": status,
                "message": message,
                "last_run": last_run["timestamp"],
                "success_rate": success_rate,
                "time_since_last_run_hours": time_since_last.total_seconds() / 3600,
                "recent_runs": len(recent_runs),
                "last_run_details": last_run
            }
            
        except Exception as e:
            logger.error(f"Failed to get collection health status: {str(e)}")
            return {
                "status": "error",
                "message": f"Error checking health: {str(e)}",
                "last_run": None,
                "success_rate": 0
            }
    
    def get_accuracy_statistics(self, days_back: int = 30) -> Dict[str, Any]:
        """
        Get forecast accuracy statistics for the specified period.
        
        Args:
            days_back (int): Number of days to look back.
            
        Returns:
            Dict[str, Any]: Accuracy statistics.
        """
        try:
            config = self.db.query(Config).filter(Config.key == "FORECAST_ACCURACY_HISTORY").first()
            
            if not config:
                return {
                    "overall_accuracy": 0,
                    "total_comparisons": 0,
                    "currency_breakdown": {},
                    "period_days": days_back
                }
            
            history = json.loads(config.value)
            
            # Filter for the specified period
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            recent_data = [
                record for record in history
                if datetime.fromisoformat(record["timestamp"]) >= cutoff_date
            ]
            
            if not recent_data:
                return {
                    "overall_accuracy": 0,
                    "total_comparisons": 0,
                    "currency_breakdown": {},
                    "period_days": days_back
                }
            
            # Calculate overall accuracy
            total_comparisons = len(recent_data)
            accurate_predictions = sum(1 for record in recent_data if record.get("accuracy_match", False))
            overall_accuracy = (accurate_predictions / total_comparisons) * 100
            
            # Calculate per-currency accuracy
            currency_stats = {}
            for record in recent_data:
                currency = record["currency"]
                if currency not in currency_stats:
                    currency_stats[currency] = {"total": 0, "accurate": 0}
                
                currency_stats[currency]["total"] += 1
                if record.get("accuracy_match", False):
                    currency_stats[currency]["accurate"] += 1
            
            # Convert to percentages
            currency_breakdown = {}
            for currency, stats in currency_stats.items():
                accuracy_pct = (stats["accurate"] / stats["total"]) * 100
                currency_breakdown[currency] = {
                    "accuracy": accuracy_pct,
                    "total_comparisons": stats["total"],
                    "accurate_predictions": stats["accurate"]
                }
            
            return {
                "overall_accuracy": overall_accuracy,
                "total_comparisons": total_comparisons,
                "accurate_predictions": accurate_predictions,
                "currency_breakdown": currency_breakdown,
                "period_days": days_back
            }
            
        except Exception as e:
            logger.error(f"Failed to get accuracy statistics: {str(e)}")
            return {
                "overall_accuracy": 0,
                "total_comparisons": 0,
                "currency_breakdown": {},
                "period_days": days_back,
                "error": str(e)
            }
    
    def _check_failure_patterns(self) -> None:
        """
        Check for concerning failure patterns and trigger alerts if needed.
        """
        try:
            health_status = self.get_collection_health_status()
            
            # Define alerting thresholds
            critical_success_rate_threshold = 30  # Alert if success rate < 30%
            warning_success_rate_threshold = 60   # Alert if success rate < 60%
            max_hours_without_run = 12           # Alert if no run in 12 hours
            
            should_alert = False
            alert_level = "info"
            alert_message = ""
            
            if health_status["status"] == "critical":
                should_alert = True
                alert_level = "critical"
                alert_message = f"🚨 CRITICAL: Actual data collection - {health_status['message']}"
            elif health_status["status"] == "warning":
                should_alert = True
                alert_level = "warning"
                alert_message = f"⚠️ WARNING: Actual data collection - {health_status['message']}"
            
            if should_alert:
                logger.warning(f"Failure pattern detected: {alert_message}")
                # Store alert for potential Discord notification
                self._store_alert(alert_level, alert_message, health_status)
        
        except Exception as e:
            logger.error(f"Failed to check failure patterns: {str(e)}")
    
    def _store_alert(self, level: str, message: str, context: Dict[str, Any]) -> None:
        """
        Store an alert for potential notification.
        
        Args:
            level (str): Alert level (info, warning, critical).
            message (str): Alert message.
            context (Dict[str, Any]): Additional context information.
        """
        try:
            timestamp = datetime.utcnow().isoformat()
            alert_data = {
                "timestamp": timestamp,
                "level": level,
                "message": message,
                "context": context
            }
            
            # Get existing alerts or create new
            config = self.db.query(Config).filter(Config.key == "ACTUAL_DATA_ALERTS").first()
            
            if config:
                # Parse existing alerts
                alerts = json.loads(config.value)
                # Add new alert
                alerts.append(alert_data)
                # Keep only last 20 alerts
                if len(alerts) > 20:
                    alerts = alerts[-20:]
                # Update config
                config.value = json.dumps(alerts)
            else:
                # Create new alerts
                config = Config(
                    key="ACTUAL_DATA_ALERTS",
                    value=json.dumps([alert_data])
                )
                self.db.add(config)
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Failed to store alert: {str(e)}")

def get_monitoring_stats() -> Dict[str, Any]:
    """
    Get comprehensive monitoring statistics for actual data functionality.
    
    Returns:
        Dict[str, Any]: Complete monitoring statistics.
    """
    try:
        with ActualDataMonitor() as monitor:
            health_status = monitor.get_collection_health_status()
            accuracy_stats = monitor.get_accuracy_statistics()
            
            return {
                "collection_health": health_status,
                "accuracy_statistics": accuracy_stats,
                "last_updated": datetime.utcnow().isoformat()
            }
    except Exception as e:
        logger.error(f"Failed to get monitoring stats: {str(e)}")
        return {
            "collection_health": {"status": "error", "message": str(e)},
            "accuracy_statistics": {"overall_accuracy": 0, "total_comparisons": 0},
            "last_updated": datetime.utcnow().isoformat(),
            "error": str(e)
        } 