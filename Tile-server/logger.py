"""
Centralized logging configuration for the Tile Server.
"""
import logging
import sys
import os
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

# Create logs directory if it doesn't exist
log_dir = Path(__file__).parent / "logs"
log_dir.mkdir(exist_ok=True)

# Configure the root logger
def setup_logger(name=None, level=None):
    """
    Set up logger with file and console handlers.
    
    Args:
        name: Logger name (None for root logger)
        level: Logging level (None uses environment or defaults to INFO)
    
    Returns:
        Configured logger
    """
    # Determine log level (environment var takes precedence)
    if level is None:
        level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    
    # Get the logger
    logger = logging.getLogger(name)
    
    # Prevent adding handlers if they already exist
    if logger.handlers:
        return logger
    
    # Set log level
    logger.setLevel(getattr(logging, level))
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level))
    
    # Create file handler with rotation (new file each day, keep 30 days)
    log_file = log_dir / f"{name or 'tileserver'}.log"
    file_handler = TimedRotatingFileHandler(
        filename=log_file,
        when="midnight",
        interval=1,
        backupCount=30,
    )
    file_handler.setLevel(getattr(logging, level))
    
    # Create and set formatter for both handlers
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    return logger

# Setup the root logger by default
root_logger = setup_logger()
