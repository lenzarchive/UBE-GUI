# -*- coding: utf-8 -*-
"""
UnityBundleExtractor - Task Queue Module
Author: lenzarchive (https://github.com/lenzarchive)
License: MIT License

This module implements the central task queue for asynchronous processing
of Unity asset bundles. Tasks (session IDs) are added here and consumed by workers.
It uses collections.deque for efficient task management and position lookup.
"""

from collections import deque
import logging
import threading

# Configure logger for this module
logger = logging.getLogger(__name__)

# The global task queue instance
processing_task_queue = deque()
# A lock to protect access to the deque from multiple threads (API route, workers)
queue_lock = threading.Lock() 

def add_task_to_queue(session_id: str):
    """
    Adds a session ID to the processing queue.

    Args:
        session_id (str): The unique identifier of the session to be processed.
    """
    with queue_lock:
        processing_task_queue.append(session_id)
        logger.info(f"Session {session_id} added to the processing queue. Current queue size: {len(processing_task_queue)}")

def get_task_from_queue() -> str:
    """
    Retrieves a session ID from the processing queue. This call is non-blocking.

    Returns:
        str: The session ID retrieved from the queue, or None if the queue is empty.
    """
    with queue_lock:
        if not processing_task_queue:
            return None
        session_id = processing_task_queue.popleft()
        logger.info(f"Session {session_id} retrieved from queue for processing. Remaining queue size: {len(processing_task_queue)}")
        return session_id

def get_queue_size() -> int:
    """
    Returns the current number of items in the processing queue.

    Returns:
        int: The number of items in the queue.
    """
    with queue_lock:
        return len(processing_task_queue)

def get_task_position(session_id: str) -> int:
    """
    Returns the 1-based position of a session ID in the queue.

    Args:
        session_id (str): The unique identifier of the session.

    Returns:
        int: The 1-based position, or -1 if the session is not found in the queue (e.g., already processed).
    """
    with queue_lock:
        try:
            return processing_task_queue.index(session_id) + 1
        except ValueError:
            return -1 # Session not found in queue

def cancel_task_in_queue(session_id: str) -> bool:
    """
    Removes a specific session from the queue if it is pending.

    Args:
        session_id (str): The ID of the session to cancel.

    Returns:
        bool: True if the task was found and removed, False otherwise.
    """
    with queue_lock:
        try:
            processing_task_queue.remove(session_id)
            logger.info(f"Session {session_id} cancelled and removed from queue. Current queue size: {len(processing_task_queue)}")
            return True
        except ValueError:
            logger.debug(f"Attempted to cancel session {session_id}, but it was not found in the queue.")
            return False