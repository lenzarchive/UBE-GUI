# -*- coding: utf-8 -*-
"""
UnityBundleExtractor - Worker Pool Module
Author: lenzarchive (https://github.com/lenzarchive)
License: MIT License

This module manages a pool of worker threads that continuously pull and process
tasks (bundle analysis/extraction) from the global task queue.
"""

import threading
import logging
import time

from flask import Flask, current_app
from .task_queue import get_task_from_queue, get_queue_size
from src.session.manager import get_session_data, update_session_status

# Configure logger for this module
logger = logging.getLogger(__name__)

class WorkerPool:
    """
    Manages a pool of background worker threads. Each worker continuously
    fetches tasks from the shared task queue and processes them.
    """
    def __init__(self, app: Flask, num_workers: int = 2):
        """
        Initializes the WorkerPool.

        Args:
            app (Flask): The Flask application instance. This is needed to push
                         application context to worker threads.
            num_workers (int): The number of worker threads to create.
        """
        self.app = app
        self.num_workers = num_workers
        self.workers = []
        self.is_running = True # Control flag for workers to stop gracefully
        logger.info(f"Worker pool initialized with {num_workers} workers.")

    def start_workers(self):
        """
        Starts the worker threads. Each worker is a daemon thread, meaning it will
        exit automatically when the main application thread exits.
        """
        for i in range(self.num_workers):
            worker_thread = threading.Thread(target=self._worker_task, args=(i,), daemon=True, name=f"BundleWorker-{i}")
            self.workers.append(worker_thread)
            worker_thread.start()
            logger.debug(f"Worker thread {i} started.")
        logger.info(f"{self.num_workers} worker threads have been launched.")

    def _worker_task(self, worker_id: int):
        """
        The main task executed by each worker thread.
        It continuously pulls session IDs from the queue and processes them.
        """
        with self.app.app_context():
            logger.info(f"Worker {worker_id} started listening for tasks.")
            while self.is_running:
                session_id = None
                try:
                    # Polling the queue, as deque.popleft() is not blocking
                    if get_queue_size() > 0:
                        session_id = get_task_from_queue()
                    
                    if session_id:
                        logger.info(f"Worker {worker_id} picked up task for session {session_id}.")
                        
                        session_data = get_session_data(session_id)
                        if not session_data or 'processor' not in session_data:
                            logger.warning(f"Worker {worker_id}: Session data for {session_id} not found or incomplete. Skipping task.")
                            continue

                        processor = session_data['processor']
                        
                        # Check if the task was already marked as cancelled before starting full processing
                        if processor._is_cancelled:
                            logger.info(f"Worker {worker_id}: Session {session_id} was already marked as cancelled. Skipping processing.")
                            processor.processing_status = "cancelled"
                            processor.error_message = "Task skipped: cancelled before processing started."
                            processor.cleanup() # Ensure cleanup for skipped task
                            continue

                        # Call the analysis method, which internally handles status updates and cancellation checks
                        processor.analyze_bundle()
                        
                        logger.info(f"Worker {worker_id} finished processing for session {session_id}. Final Status: {processor.processing_status}")
                        
                    else:
                        # If queue is empty, wait for a short period before checking again
                        time.sleep(0.5)
                        
                except InterruptedError: # Caught if processor itself raises InterruptedError on cancellation
                    logger.info(f"Worker {worker_id}: Session {session_id} processing interrupted by cancellation.")
                    # Processor already updated its status and cleaned up
                except Exception as e:
                    logger.error(f"Worker {worker_id} encountered an error processing session {session_id or 'unknown'}: {e}", exc_info=True)
                    if session_id:
                        session_data = get_session_data(session_id)
                        if session_data and 'processor' in session_data:
                            processor = session_data['processor']
                            if processor.processing_status not in ["cancelled", "error"]: # Avoid overwriting explicit cancellation
                                processor.processing_status = "error"
                                processor.error_message = f"Worker processing error: {str(e)}"
                                update_session_status(session_id, 'processing_status', 'error')
                                update_session_status(session_id, 'error_message', processor.error_message)
                        else:
                            logger.critical(f"Worker {worker_id}: Could not update status for session {session_id} due to missing session data after error.")
                finally:
                    # In a deque based queue, task_done() is not used.
                    # The task is considered done once it's popped from the queue.
                    pass

    def stop_workers(self):
        """
        Signals all worker threads to stop.
        This is typically called during graceful application shutdown.
        """
        self.is_running = False
        for worker_thread in self.workers:
            worker_thread.join(timeout=1.0)
            if worker_thread.is_alive():
                logger.warning(f"Worker thread {worker_thread.name} did not terminate gracefully.")
        logger.info("Worker pool stopped.")