# -*- coding: utf-8 -*-
"""
UnityBundleExtractor - Flask API Routes Module
Author: lenzarchive (https://github.com/lenzarchive)
License: MIT License

This module defines all the API endpoints for the UnityBundleExtractor web interface.
It handles file uploads, displays analysis status, initiates asset extraction, and manages downloads.
"""

import os
import shutil
import uuid
import threading
import json
import traceback
import logging
from datetime import datetime, timedelta
import time
from typing import Tuple

from flask import Blueprint, request, jsonify, send_file, current_app, render_template, after_this_request
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge

from src.config import Config
from src.utils import is_allowed_file_extension, get_file_info
from src.bundle_processing.core_processor import BundleProcessor
from src.session.manager import get_session_data, add_session_data, update_session_status, get_session_lock, remove_session_data
from src.queue_manager.task_queue import add_task_to_queue, get_queue_size, get_task_position, cancel_task_in_queue

# Create a Blueprint for API routes
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Configure logger for this module
logger = logging.getLogger(__name__)

# In-memory dictionary for rate limiting
last_request_times = {}
rate_limit_lock = threading.Lock()

def _check_rate_limit(ip_address: str) -> Tuple[bool, int]:
    """
    Checks if an IP address is exceeding the configured rate limit.

    Args:
        ip_address (str): The IP address of the client.

    Returns:
        Tuple[bool, int]: A tuple where the first element is True if rate limited, False otherwise.
                          The second element is the 'Retry-After' duration in seconds if rate limited.
    """
    if not Config.RATE_LIMIT_ENABLED:
        return False, 0

    with rate_limit_lock:
        current_time = time.time()
        # Remove old requests outside the window
        last_request_times[ip_address] = [
            t for t in last_request_times.get(ip_address, [])
            if current_time - t < Config.RATE_LIMIT_WINDOW_SECONDS
        ]

        if len(last_request_times[ip_address]) >= Config.RATE_LIMIT_PER_MINUTE:
            # Calculate when the client can retry
            oldest_request_time = last_request_times[ip_address][0]
            retry_after = int(Config.RATE_LIMIT_WINDOW_SECONDS - (current_time - oldest_request_time))
            return True, max(1, retry_after)
        
        last_request_times[ip_address].append(current_time)
        return False, 0

@api_bp.route('/')
def index_root():
    """
    Serves the main `index.html` page for the web interface when accessing /api/.
    This route primarily exists to catch direct access to /api/ and redirect or serve a message.
    The primary index route is handled by app.py's root '/'.
    """
    return render_template('index.html')

@api_bp.route('/upload', methods=['POST'])
def upload_bundle():
    """
    Handles file uploads from the client.
    It saves all submitted files to a unique session directory, identifies
    the primary Unity bundle file, and adds the processing task to a queue.
    This endpoint is rate-limited.

    Returns:
        JSON response: Contains session_id and status, or an error message.
    """
    # Apply rate limiting
    client_ip = request.remote_addr
    is_rate_limited, retry_after = _check_rate_limit(client_ip)
    if is_rate_limited:
        logger.warning(f"Rate limit exceeded for IP: {client_ip}")
        response = jsonify({
            'error': f"Too many requests. Please try again after {retry_after} seconds. Limit: {Config.RATE_LIMIT_PER_MINUTE} requests per minute."
        })
        response.headers['Retry-After'] = str(retry_after)
        return response, 429

    if 'files' not in request.files:
        logger.warning("Upload attempt without 'files' part in request.")
        return jsonify({'error': 'No file part in the request'}), 400
    
    files = request.files.getlist('files')
    if not files or not files[0].filename:
        logger.warning("Upload attempt without selected file.")
        return jsonify({'error': 'No file selected for uploading'}), 400

    session_id = str(uuid.uuid4())
    session_upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], session_id)
    os.makedirs(session_upload_dir, exist_ok=True)
    
    try:
        all_uploaded_files = []
        for file_item in files:
            if file_item and file_item.filename:
                if not is_allowed_file_extension(file_item.filename, current_app.config['ALLOWED_EXTENSIONS']):
                    shutil.rmtree(session_upload_dir, ignore_errors=True)
                    logger.warning(f"Invalid file type uploaded: {file_item.filename}")
                    return jsonify({
                        'error': f'Invalid file type: {file_item.filename}. Allowed extensions are: {", ".join(current_app.config["ALLOWED_EXTENSIONS"])}'
                    }), 400

                filename_secured = secure_filename(file_item.filename)
                save_path = os.path.join(session_upload_dir, filename_secured)
                file_item.save(save_path)
                all_uploaded_files.append({'path': save_path, 'name': file_item.filename})
        
        primary_file = None
        bundle_extensions = ['.bundle', '.unity3d', '.assets', '.unitybundle', '.assetbundle']
        for f in all_uploaded_files:
            if any(f['name'].lower().endswith(ext) for ext in bundle_extensions):
                primary_file = f
                break
        
        if not primary_file:
            for f in all_uploaded_files:
                 if f['name'].lower().endswith('.assets'):
                    primary_file = f
                    break
        
        if not primary_file:
            shutil.rmtree(session_upload_dir, ignore_errors=True)
            logger.error("Upload failed: No main Unity bundle/asset file found among selected files.")
            raise ValueError("No main Unity bundle/asset file (.bundle, .unity3d, .assets, .unitybundle, .assetbundle) was found in the upload.")

        send_log = request.form.get('send_log') == 'true'
        allow_retention = request.form.get('allow_storage') == 'true'

        # Create a BundleProcessor instance and set its initial status to 'queued'
        processor = BundleProcessor(session_id, primary_file['path'], primary_file['name'], session_upload_dir, current_app.config, send_log, allow_retention)
        processor.processing_status = "queued"
        
        # Add the processor instance to the global session manager
        add_session_data(session_id, processor)
        
        # Add the session ID to the task queue for a worker to pick up
        add_task_to_queue(session_id)
        
        logger.info(f"Upload successful for session {session_id}. Task added to queue.")
        # Return 'queued' status along with current queue info
        return jsonify({
            'session_id': session_id,
            'status': 'queued',
            'queue_position': get_task_position(session_id),
            'total_queue_size': get_queue_size()
        })

    except RequestEntityTooLarge:
        shutil.rmtree(session_upload_dir, ignore_errors=True)
        logger.error(f"Upload failed: File size exceeds limit of {current_app.config['MAX_CONTENT_LENGTH'] // 1024 // 1024}MB.")
        return jsonify({'error': f'File size exceeds the limit of {current_app.config["MAX_CONTENT_LENGTH"] // 1024 // 1024}MB'}), 413
    except Exception as e:
        shutil.rmtree(session_upload_dir, ignore_errors=True)
        logger.error(f"Upload failed for session {session_id}: {e}", exc_info=True)
        return jsonify({'error': f'An unexpected error occurred during upload: {e}'}), 500

@api_bp.route('/status/<session_id>')
def get_status(session_id: str):
    """
    Polls for the current status of an ongoing bundle analysis session.
    Provides progress updates, metadata upon completion, or error messages.
    Also returns queue position if the task is still queued.

    Args:
        session_id (str): The ID of the session to check.

    Returns:
        JSON response: Current status, progress, and potentially metadata or error,
                       plus queue information if applicable.
    """
    session_data = get_session_data(session_id)
    
    if not session_data or 'processor' not in session_data:
        logger.warning(f"Status check requested for non-existent or expired session: {session_id}")
        return jsonify({'error': 'Session not found or expired'}), 404
    
    processor = session_data['processor']
    response = {'status': processor.processing_status, 'progress': processor.progress}
    
    # Add queue-specific information if the task is still in the 'queued' state
    if processor.processing_status == 'queued':
        response['queue_position'] = get_task_position(session_id)
        response['total_queue_size'] = get_queue_size()
        
    if processor.processing_status == 'completed':
        response['metadata'] = processor.metadata
    elif processor.processing_status == 'error':
        response['error'] = processor.error_message
    elif processor.processing_status == 'cancelled':
        response['error'] = processor.error_message # For cancelled, provide error message (e.g. "Task cancelled by user.")
        
    logger.debug(f"Status for session {session_id}: {processor.processing_status} ({processor.progress}%)")
    return jsonify(response)

@api_bp.route('/extract', methods=['POST'])
def extract_assets():
    """
    Initiates the asset extraction process for a given session and a list of
    selected asset indices. This process runs in a background thread.

    Request JSON Body:
        {
            "session_id": "uuid-string",
            "selected_assets": [123, 456, 789] # List of asset indices
        }

    Returns:
        JSON response: Status indicating if extraction has started or an error message.
    """
    data = request.get_json()
    session_id = data.get('session_id')
    selected_indices = data.get('selected_assets')

    if not all([session_id, isinstance(selected_indices, list)]):
        logger.warning(f"Extraction request missing session_id or selected_assets: {data}")
        return jsonify({'error': 'Missing session_id or selected_assets in request body'}), 400

    session_data = get_session_data(session_id)
    
    if not session_data or 'processor' not in session_data:
        logger.warning(f"Extraction requested for non-existent or expired session: {session_id}")
        return jsonify({'error': 'Session not found or expired'}), 404
    
    processor = session_data['processor']

    # Directly call extract_selected_assets in a new thread
    # We pass current_app._get_current_object() to ensure it has context.
    threading.Thread(target=_extract_assets_async_task, args=(current_app._get_current_object(), processor, session_id, selected_indices), name=f"ExtractionThread-{session_id}").start()
    
    logger.info(f"Extraction initiated for session {session_id} with {len(selected_indices)} assets.")
    return jsonify({'status': 'extraction_started'})

def _extract_assets_async_task(app_instance, processor, session_id, selected_indices):
    """
    A standalone function to run extraction in a separate thread.
    Pushes an application context to allow Flask functionality access.
    """
    with app_instance.app_context():
        try:
            zip_path = processor.extract_selected_assets(selected_indices)
            update_session_status(session_id, 'zip_path', zip_path)
            update_session_status(session_id, 'extraction_completed_at', datetime.now().isoformat())
        except InterruptedError:
            # Task was cancelled, status already set by processor. Just log.
            logger.info(f"Async extraction task for session {session_id} was interrupted by cancellation.")
        except Exception as e:
            logger.error(f"Async extraction task failed for session {session_id}: {e}", exc_info=True)
            # Ensure status is updated to error if not already cancelled
            if processor.processing_status != "cancelled":
                update_session_status(session_id, 'processing_status', 'error')

@api_bp.route('/extraction-status/<session_id>')
def get_extraction_status(session_id: str):
    """
    Polls for the status of an ongoing asset extraction task.
    Provides progress, and indicates when the download is ready.

    Args:
        session_id (str): The ID of the session to check.

    Returns:
        JSON response: Current status, progress, download readiness, or error.
    """
    session_data = get_session_data(session_id)
    
    if not session_data or 'processor' not in session_data:
        logger.warning(f"Extraction status requested for non-existent or expired session: {session_id}")
        return jsonify({'error': 'Session not found or expired'}), 404
    
    processor = session_data['processor']
    status = processor.processing_status
    progress = processor.progress
    
    response = {'status': status, 'progress': progress}
    if status == 'completed' and 'zip_path' in session_data:
        response['download_ready'] = True
    elif status == 'error':
        response['error'] = processor.error_message
    elif status == 'cancelled': # Include cancelled status in response
        response['error'] = processor.error_message
        
    logger.debug(f"Extraction status for session {session_id}: {status} ({progress}%)")
    return jsonify(response)
    
@api_bp.route('/download/<session_id>')
def download_assets(session_id: str):
    """
    Serves the final ZIP archive containing the extracted assets for download.
    This endpoint is called once extraction is complete and download_ready is True.
    It also triggers cleanup if file retention is not allowed.

    Args:
        session_id (str): The ID of the session for which to download the ZIP.

    Returns:
        Response: The ZIP file as an attachment, or an error JSON.
    """
    session_data = get_session_data(session_id)

    if not session_data or 'zip_path' not in session_data:
        logger.warning(f"Download requested for session {session_id} but ZIP not ready or session expired.")
        return jsonify({'error': 'Download not ready or session expired'}), 404

    zip_path = session_data['zip_path']
    if not os.path.exists(zip_path):
        logger.error(f"Download file not found at {zip_path} for session {session_id}. May have been cleaned up prematurely.")
        return jsonify({'error': 'File not found, may have been cleaned up'}), 404
    
    processor = session_data.get('processor')
    if processor and not processor.allow_retention:
        @after_this_request
        def cleanup_session(response):
            try:
                logger.info(f"Triggering immediate cleanup for session {session_id} after download.")
                processor.cleanup()
                remove_session_data(session_id)
            except Exception as e:
                logger.error(f"Error during post-download cleanup for session {session_id}: {e}", exc_info=True)
            return response

    logger.info(f"Serving download for session {session_id} from {zip_path}.")
    return send_file(zip_path, as_attachment=True, download_name=os.path.basename(zip_path))

# Queue management API endpoints
@api_bp.route('/queue/cancel', methods=['POST'])
def cancel_queue_task():
    """
    Cancels a specific task. If the task is in the queue, it's removed.
    If it's processing, a cancellation flag is set for the worker to detect.

    Request JSON Body:
        {
            "session_id": "uuid-string"
        }
    """
    session_id = request.json.get('session_id')
    if not session_id:
        return jsonify({'error': 'Session ID is required.'}), 400

    session_data = get_session_data(session_id)
    if not session_data or 'processor' not in session_data:
        logger.warning(f"Attempted to cancel session {session_id}, but it was not found in active sessions.")
        return jsonify({'error': 'Task not found or already completed.'}), 404
    
    processor = session_data['processor']
    
    # Set cancellation flag on the processor instance
    processor._is_cancelled = True
    
    # Attempt to remove from the queue first (if it hasn't been picked up yet)
    was_removed_from_queue = cancel_task_in_queue(session_id)
    
    if was_removed_from_queue:
        # If successfully removed from queue, set final status and cleanup
        processor.processing_status = "cancelled"
        processor.error_message = "Task cancelled by user (removed from queue)."
        processor.cleanup() # Clean up files for tasks cancelled in queue
        logger.info(f"Session {session_id} cancelled and removed from queue by user.")
        return jsonify({'status': 'success', 'message': f'Task {session_id} cancelled.'}), 200
    else:
        if processor.processing_status not in ["completed", "error"]: # Don't overwrite final statuses
            processor.processing_status = "cancelling"
            processor.error_message = "Task cancellation requested (processing in progress)."
        logger.info(f"Session {session_id} cancellation requested (was already processing).")
        return jsonify({'status': 'success', 'message': f'Task {session_id} cancellation initiated.'}), 200