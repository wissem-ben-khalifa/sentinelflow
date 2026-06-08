"""
SentinelFlow - Logging Configuration
Every module imports this to get consistent logging.
"""

import logging
import sys
from pathlib import Path
from config.settings import LOG_LEVEL, LOG_DIR


def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger for the given module name.
    Logs to both console and file.
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    log_file = LOG_DIR / "sentinelflow.log"
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger