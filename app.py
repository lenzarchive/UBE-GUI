# -*- coding: utf-8 -*-
"""
UnityBundleExtractor - Main Flask Application Entry Point
Author: lenzarchive (https://github.com/lenzarchive)
License: MIT License

This file serves as the main entry point for the UnityBundleExtractor web application.
It initializes the Flask application, configures global settings, registers API blueprints,
and starts background tasks and worker pools.
"""

import os
import logging
from logging.handlers import RotatingFileHandler

from flask import Flask, render_template

from src.config import Config
from src.api.routes import api_bp
from src.api.error_handlers import register_error_handlers
from src.session.manager import processing_sessions, session_lock, initialize_session_manager
from src.tasks.scheduler import start_cleanup_scheduler
from src.queue_manager.worker_pool import WorkerPool

# Initialize Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Configure global logger
if not os.path.exists('logs'):
    os.makedirs('logs')

global_log_handler = RotatingFileHandler(
    os.path.join('logs', Config.GLOBAL_LOG_FILE),
    maxBytes=10 * 1024 * 1024,  # 10 MB per file
    backupCount=5
)
global_log_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))
global_log_handler.setLevel(getattr(logging, Config.GLOBAL_LOG_LEVEL))

app.logger.addHandler(global_log_handler)
app.logger.setLevel(getattr(logging, Config.GLOBAL_LOG_LEVEL))
app.logger.info("UnityBundleExtractor Web global logger initialized.")

# Get a logger for the main app module
main_logger = logging.getLogger(__name__)
main_logger.addHandler(global_log_handler)
main_logger.setLevel(getattr(logging, Config.GLOBAL_LOG_LEVEL))

# Initialize the global session manager with Flask app context
initialize_session_manager(app, processing_sessions, session_lock)

# Register primary index route at the root level '/'
@app.route('/')
def index():
    """
    Serves the main `index.html` page for the web interface at the root URL.
    """
    return render_template('index.html')

# Register API routes blueprint
app.register_blueprint(api_bp)

# Register global error handlers
register_error_handlers(app)

# Main execution block
if __name__ == '__main__':
    # Ensure necessary runtime directories exist on startup
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    os.makedirs(Config.SESSION_LOGS_DIR, exist_ok=True)
    
    # Start the background cleanup scheduler
    start_cleanup_scheduler(app)
    
    # Initialize and start the worker pool for processing tasks from the queue
    num_workers = int(os.environ.get('WEB_CONCURRENCY', 2)) # Use WEB_CONCURRENCY for workers, default 2
    worker_pool = WorkerPool(app, num_workers=num_workers)
    worker_pool.start_workers() # Workers will start pulling tasks from the queue
    
    # Run the Flask development server
    app.run(
        debug=Config.DEBUG_MODE,
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000))
    )