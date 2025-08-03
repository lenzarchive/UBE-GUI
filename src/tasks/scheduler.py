# -*- coding: utf-8 -*-
"""
UnityBundleExtractor - Background Scheduler Module
Author: lenzarchive (https://github.com/lenzarchive)
License: MIT License

This module defines the standalone function for starting a background daemon thread
that periodically runs the cleanup task.
"""

import time
import threading
import logging
from flask import Flask

from .cleanup import cleanup_old_files

logger = logging.getLogger(__name__)

def start_cleanup_scheduler(app: Flask):
    """
    Starts a daemon thread that periodically runs the cleanup task.
    This thread will run in the background as long as the main application is running.

    Args:
        app (Flask): The Flask application instance to access configuration and pass to cleanup.
    """
    def task():
        with app.app_context():
            while True:
                time.sleep(app.config['CLEANUP_INTERVAL'])
                try:
                    cleanup_old_files(app)
                except Exception as e:
                    logger.error(f"Error in cleanup scheduler thread: {e}", exc_info=True)
    
    threading.Thread(target=task, daemon=True, name="CleanupScheduler").start()
    logger.info(f"Cleanup scheduler started with interval {app.config['CLEANUP_INTERVAL']} seconds.")