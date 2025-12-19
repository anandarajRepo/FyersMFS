# utils/logger.py

"""
Logging configuration for MMFS strategy
"""

import logging
import sys
from datetime import datetime
from pathlib import Path
from config.settings import LogConfig, TradingConfig


def setup_logger(name: str = 'mmfs', log_to_file: bool = True):
    """
    Setup logger with console and file handlers

    Args:
        name: Logger name
        log_to_file: Whether to log to file

    Returns:
        Logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, TradingConfig.LOG_LEVEL))

    # Remove existing handlers
    logger.handlers = []

    # Create formatters
    console_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # File handler
    if log_to_file or TradingConfig.LOG_TO_FILE:
        # Create logs directory if it doesn't exist
        log_dir = Path(LogConfig.LOG_DIR)
        log_dir.mkdir(exist_ok=True)

        # Create log file with date
        log_file = log_dir / f"{LogConfig.LOG_FILE_PREFIX}_{datetime.now().strftime('%Y%m%d')}.log"

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def get_logger(name: str):
    """Get logger by name"""
    return logging.getLogger(name)


if __name__ == "__main__":
    # Test logger
    logger = setup_logger('test')

    logger.debug("Debug message")
    logger.info("Info message")
    logger.warning("Warning message")
    logger.error("Error message")

    print("\n✓ Logger test complete. Check logs/ directory for log file.")