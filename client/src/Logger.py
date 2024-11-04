"""Logger module for handling application-wide logging configuration."""

import logging
import os
from datetime import datetime
from typing import Optional

LOG_DIR = "client_logs"
_logger: Optional[logging.Logger] = None

def setup_logger(name: str) -> logging.Logger:
    """
    Configure and return a logger instance.
    
    Args:
        name: The name of the module requesting the logger.
        
    Returns:
        logging.Logger: Configured logger instance.
    """
    global _logger
    
    if _logger is not None:
        return logging.getLogger(name)
        
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    log_file: str = os.path.join(
        LOG_DIR, f"Client_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )

    _logger = logging.getLogger(name)
    _logger.info("Logger setup complete")
    
    return _logger 