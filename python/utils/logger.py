# logger.py — Centralised logging for all Charli modules

import logging
import os
from datetime import datetime
from config import LOG_DIR, APP_NAME, DEBUG_MODE

def get_logger(module_name: str) -> logging.Logger:
    """
    Returns a configured logger for the given module.
    Logs to both console and a daily rotating log file.
    
    Usage:
        from utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Something happened")
    """
    logger = logging.getLogger(module_name)

    # Avoid adding duplicate handlers if logger already exists
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)

    # ── Console handler ────────────────────────────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG if DEBUG_MODE else logging.INFO)
    console_format = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] %(name)s — %(message)s",
        datefmt="%H:%M:%S"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # ── File handler ───────────────────────────────────────────────────────
    log_filename = datetime.now().strftime(f"{APP_NAME}_%Y-%m-%d.log")
    log_filepath = os.path.join(LOG_DIR, log_filename)

    file_handler = logging.FileHandler(log_filepath, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    return logger