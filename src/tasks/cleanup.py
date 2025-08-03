# -*- coding: utf-8 -*-
"""
UnityBundleExtractor - Cleanup Task Module
Author: lenzarchive (https://github.com/lenzarchive)
License: MIT License

This module defines the standalone function for cleaning up old session files and directories.
"""

import os
import shutil
import logging
from datetime import datetime, timedelta
from flask import Flask

from src.session.manager import get_all_sessions, remove_session_data, get_session_lock

logger = logging.getLogger(__name__)

def cleanup_old_files(app: Flask):
    """
    Iterates through active processing sessions and temporary directories,
    removing those that are older than the configured retention period.
    This helps manage disk space and ensures temporary files don't persist indefinitely.

    Args:
        app (Flask): The Flask application instance to access configuration.
    """
    logger.info("Starting cleanup of old files and sessions.")
    
    file_retention_hours = app.config['FILE_RETENTION_HOURS']
    cutoff = datetime.now() - timedelta(hours=file_retention_hours)
    
    sessions_to_check = get_all_sessions()
    session_lock_obj = get_session_lock()

    with session_lock_obj:
        expired_ids = [sid for sid, data in sessions_to_check.items()
                       if datetime.fromisoformat(data['created_at']) < cutoff]
        for session_id in expired_ids:
            session_data = sessions_to_check.get(session_id)
            if session_data and 'processor' in session_data:
                processor = session_data['processor']
                processor.cleanup()
                remove_session_data(session_id)
                logger.info(f"Cleaned up expired session: {session_id}")
    
    for folder in [app.config['UPLOAD_FOLDER'], app.config['OUTPUT_FOLDER'], app.config['SESSION_LOGS_DIR']]:
        if not os.path.exists(folder):
            continue
        for entry in os.listdir(folder):
            path = os.path.join(folder, entry)
            try:
                if datetime.fromtimestamp(os.path.getmtime(path)) < cutoff:
                    if os.path.isdir(path):
                        shutil.rmtree(path, ignore_errors=True)
                        logger.info(f"Removed old orphaned directory: {path}")
                    elif os.path.isfile(path):
                        os.remove(path)
                        logger.info(f"Removed old orphaned file: {path}")
            except Exception as e:
                logger.warning(f"Error during orphaned cleanup of {path}: {e}", exc_info=True)
    logger.info("Cleanup of old files and sessions completed.")