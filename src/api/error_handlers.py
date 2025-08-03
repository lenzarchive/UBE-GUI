# -*- coding: utf-8 -*-
"""
UnityBundleExtractor - Flask Error Handlers Module
Author: lenzarchive (https://github.com/lenzarchive)
License: MIT License

This module defines global error handlers for the Flask application.
"""

import logging
from flask import jsonify

logger = logging.getLogger(__name__)

def register_error_handlers(app):
    """
    Registers custom error handlers with the Flask application.

    Args:
        app (Flask): The Flask application instance.
    """
    @app.errorhandler(413)
    def request_entity_too_large(e):
        """Handler for HTTP 413 Request Entity Too Large errors."""
        logger.error(f"Request Entity Too Large: {e.description}")
        return jsonify({'error': 'File size exceeds the configured limit.'}), 413

    @app.errorhandler(500)
    def internal_server_error(e):
        """Handler for HTTP 500 Internal Server Error."""
        logger.error(f"Internal Server Error: {e}", exc_info=True)
        return jsonify({'error': 'An internal server error occurred.'}), 500