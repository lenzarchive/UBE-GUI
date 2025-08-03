# -*- coding: utf-8 -*-
"""
UnityBundleExtractor - Session Logger Setup Module
Author: lenzarchive (https://github.com/lenzarchive)
License: MIT License

This module provides a standalone function to set up a dedicated logger
for individual processing sessions.
"""

import os
import logging
from logging.handlers import RotatingFileHandler

def setup_session_logger(session_id: str, base_log_dir: str, log_level: str) -> logging.Logger:
    """
    Creates and configures a dedicated logger for a specific session.
    This allows for detailed, session-specific logging without cluttering the global log.

    Args:
        session_id (str): The unique identifier for the session.
        base_log_dir (str): The base directory where session-specific logs will be stored.
        log_level (str): The logging level for the session logger (e.g., 'DEBUG', 'INFO').

    Returns:
        logging.Logger: The configured logger instance for the session.
    """
    session_log_dir = os.path.join(base_log_dir, session_id)
    os.makedirs(session_log_dir, exist_ok=True)
    
    session_logger = logging.getLogger(f"session.{session_id}")
    session_logger.propagate = False
    
    handler = RotatingFileHandler(
        os.path.join(session_log_dir, f"{session_id}.log"),
        maxBytes=2 * 1024 * 1024,  # 2 MB per file
        backupCount=1
    )
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    handler.setLevel(getattr(logging, log_level))
    
    session_logger.addHandler(handler)
    session_logger.setLevel(getattr(logging, log_level))
    
    session_logger.info(f"Session logger initialized for session ID: {session_id}")
    return session_logger