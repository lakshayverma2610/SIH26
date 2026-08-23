import logging
import json
from typing import Any, Dict
from ai_engine.core.config import settings

class JSONFormatter(logging.Formatter):
    """
    Custom formatter to output standard Python logs as JSON for 
    high-observability aggregation (e.g., ELK, Datadog).
    """
    def format(self, record: logging.LogRecord) -> str:
        log_record: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "name": record.name,
            "message": record.getMessage()
        }
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger instance with JSON formatting.
    
    Args:
        name (str): The name of the module requesting the logger.
        
    Returns:
        logging.Logger: Configured logger.
    """
    logger = logging.getLogger(name)
    
    # Only configure if handlers aren't already set to avoid duplication
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = JSONFormatter()
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        # Set level based on centralized config
        level = getattr(logging, settings.LOG_LEVEL, logging.INFO)
        logger.setLevel(level)
        
        # Prevent log propagation to the root logger
        logger.propagate = False
        
    return logger
