"""Logging configuration for the application."""

import logging
import os
from pathlib import Path
from datetime import datetime

LOG_DIR = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "gdrive-backup-manager" / "logs"

def setup_logger(name: str = "gdrive_backup") -> logging.Logger:
    """
    Initializes and returns the application logger.
    Logs to both console and a timestamped file.
    """
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    
    # Prevent adding multiple handlers if called multiple times
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # File handler
    log_file = LOG_DIR / f"backup_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger