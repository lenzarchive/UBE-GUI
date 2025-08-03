# -*- coding: utf-8 -*-
"""
UnityBundleExtractor - Session Manager Module
Author: lenzarchive (https://github.com/lenzarchive)
License: MIT License

This module provides functions for managing global processing sessions,
ensuring thread-safe access to session data.
"""

import threading
import logging
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Global dictionary to hold data for active processing sessions.
# Keys are session IDs, values are dictionaries containing BundleProcessor instances and metadata.
processing_sessions: Dict[str, Dict[str, Any]] = {}

# A lock to ensure thread-safe access to the `processing_sessions` dictionary
session_lock = threading.Lock()

def initialize_session_manager(app_instance: Any, sessions_dict: Dict[str, Any], lock_obj: threading.Lock):
    """
    Initializes the session manager by associating global session data
    and lock with the Flask application instance (if needed by context)
    and providing references to other modules.

    Args:
        app_instance (Any): The Flask application instance.
        sessions_dict (Dict[str, Any]): The global dictionary for sessions.
        lock_obj (threading.Lock): The global lock for sessions.
    """
    global processing_sessions, session_lock
    processing_sessions = sessions_dict
    session_lock = lock_obj
    logger.info("Session manager initialized.")

def get_session_data(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves data for a specific session in a thread-safe manner.

    Args:
        session_id (str): The ID of the session.

    Returns:
        Optional[Dict[str, Any]]: The session data, or None if not found.
    """
    with session_lock:
        return processing_sessions.get(session_id)

def add_session_data(session_id: str, processor_instance: Any):
    """
    Adds a new session's data to the manager in a thread-safe manner.

    Args:
        session_id (str): The ID of the new session.
        processor_instance (Any): The BundleProcessor instance for this session.
    """
    with session_lock:
        processing_sessions[session_id] = {
            'processor': processor_instance,
            'created_at': datetime.now().isoformat()
        }
    logger.debug(f"Session {session_id} added to manager.")

def update_session_status(session_id: str, key: str, value: Any):
    """
    Updates a specific key-value pair in a session's data in a thread-safe manner.

    Args:
        session_id (str): The ID of the session.
        key (str): The key to update (e.g., 'zip_path', 'extraction_completed_at').
        value (Any): The new value for the key.
    """
    with session_lock:
        if session_id in processing_sessions:
            processing_sessions[session_id][key] = value
            logger.debug(f"Session {session_id} updated: {key} = {value}")
        else:
            logger.warning(f"Attempted to update non-existent session {session_id} for key {key}.")

def remove_session_data(session_id: str):
    """
    Removes a session's data from the manager in a thread-safe manner.

    Args:
        session_id (str): The ID of the session to remove.
    """
    with session_lock:
        if session_id in processing_sessions:
            del processing_sessions[session_id]
            logger.debug(f"Session {session_id} removed from manager.")
        else:
            logger.warning(f"Attempted to remove non-existent session {session_id}.")

def get_all_sessions() -> Dict[str, Dict[str, Any]]:
    """
    Returns a copy of all active session data in a thread-safe manner.

    Returns:
        Dict[str, Dict[str, Any]]: A copy of the dictionary containing all active sessions.
    """
    with session_lock:
        return processing_sessions.copy()

def get_session_lock() -> threading.Lock:
    """
    Provides access to the global session lock.

    Returns:
        threading.Lock: The global session lock.
    """
    return session_lock