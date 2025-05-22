"""
Logging utilities for the Forex Factory Sentiment Analyzer.
"""
import logging
import sys
import json
from datetime import datetime

# Configure the root logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

class JsonFormatter(logging.Formatter):
    """
    Format logs as JSON for structured logging.
    """
    def format(self, record):
        log_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
            
        # Add extra fields if present
        if hasattr(record, "extra"):
            log_record.update(record.extra)
            
        return json.dumps(log_record)

def get_logger(name):
    """
    Get a logger with the given name.
    
    Args:
        name (str): The name of the logger.
        
    Returns:
        logging.Logger: A configured logger.
    """
    logger = logging.getLogger(name)
    return logger 