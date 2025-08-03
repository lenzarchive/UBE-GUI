# -*- coding: utf-8 -*-
"""
UnityBundleExtractor - WSGI Production Configuration
Author: lenzarchive (https://github.com/lenzarchive)
License: MIT License

WSGI configuration for production deployment of the UnityBundleExtractor Flask application.
Compatible with Gunicorn, uWSGI, and other WSGI servers.
"""

import os
import sys
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler

# Add project directory to Python path to ensure imports work correctly
project_dir = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_dir))

# Import the Flask application instance from the main app.py file
from app import app
from src.config import Config # Import configuration
from src.tasks.scheduler import start_cleanup_scheduler # Import cleanup scheduler
from src.session.manager import processing_sessions, session_lock, initialize_session_manager # Import manager for WSGI context
from src.queue_manager.worker_pool import WorkerPool # Import WorkerPool for WSGI context

# Apply production configuration directly or via environment variables
class ProductionConfig(Config):
    """
    Production-specific configuration, inheriting from base Config.
    Overrides or sets defaults for production environment variables.
    """
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-this-in-production')
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 500 * 1024 * 1024))
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    OUTPUT_FOLDER = os.environ.get('OUTPUT_FOLDER', 'extractions')
    FILE_RETENTION_HOURS = int(os.environ.get('FILE_RETENTION_HOURS', 24))
    CLEANUP_INTERVAL = int(os.environ.get('CLEANUP_INTERVAL', 3600))
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    GLOBAL_LOG_FILE = os.environ.get('GLOBAL_LOG_FILE', 'unity_extractor.log')
    WORKER_TIMEOUT = int(os.environ.get('WORKER_TIMEOUT', 300))
    MAX_WORKERS = int(os.environ.get('MAX_WORKERS', 4))
    # Number of workers for the internal queue processing pool
    WEB_CONCURRENCY = int(os.environ.get('WEB_CONCURRENCY', 2)) # Default 2 internal workers

# Apply production configuration to the Flask app instance
app.config.from_object(ProductionConfig)

# Production Logging Setup
if not app.debug:
    log_dir = 'logs'
    if not os.path.exists(log_dir):
        os.mkdir(log_dir)
    
    for handler in app.logger.handlers[:]:
        app.logger.removeHandler(handler)

    file_handler = RotatingFileHandler(
        os.path.join(log_dir, ProductionConfig.GLOBAL_LOG_FILE),
        maxBytes=10 * 1024 * 1024,
        backupCount=5
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s %(name)s %(threadName)s : %(message)s'
    ))
    file_handler.setLevel(getattr(logging, ProductionConfig.LOG_LEVEL))
    app.logger.addHandler(file_handler)
    app.logger.setLevel(getattr(logging, ProductionConfig.LOG_LEVEL))
    app.logger.info('UnityBundleExtractor Web application starting in production mode.')

# Ensure necessary directories exist on WSGI server startup
os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
os.makedirs(Config.OUTPUT_FOLDER, exist_ok=True)
os.makedirs(Config.SESSION_LOGS_DIR, exist_ok=True)

# Initialize the session manager for the WSGI context
initialize_session_manager(app, processing_sessions, session_lock)

# Start the cleanup scheduler in the WSGI context
start_cleanup_scheduler(app)
app.logger.info("Cleanup scheduler initialized and started from wsgi.py.")

# Initialize and start the worker pool for processing tasks from the queue
worker_pool = WorkerPool(app, num_workers=app.config['WEB_CONCURRENCY'])
worker_pool.start_workers()
app.logger.info(f"Worker pool started with {app.config['WEB_CONCURRENCY']} workers.")

# WSGI Application Object
application = app

# Development server (not for production use)
if __name__ == "__main__":
    app.run(
        debug=ProductionConfig.DEBUG_MODE,
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000))
    )