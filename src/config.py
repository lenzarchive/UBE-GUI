# -*- coding: utf-8 -*-
"""
UnityBundleExtractor - Configuration Module
Author: lenzarchive (https://github.com/lenzarchive)
License: MIT License

This module defines the application-wide configuration settings for the Flask application.
"""

import os
import logging

class Config:
    """
    Configuration class for the Flask application.
    Settings can be overridden by environment variables for flexible deployment.
    """
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 500 * 1024 * 1024))  # 500 MB
    UPLOAD_FOLDER = 'uploads'
    OUTPUT_FOLDER = 'extractions'
    ALLOWED_EXTENSIONS = {
        'bundle', 'unity3d', 'assets', 'unitybundle', 'assetbundle', 'ress', 
        'resource', 'dat', 'bin', 'txt', 'bytes', 'json', 'xml', 'yaml', 
        'csv', 'shader', 'font', 'audio', 'video'
    }

    CLEANUP_INTERVAL = int(os.environ.get('CLEANUP_INTERVAL', 3600))  # 1 hour in seconds
    FILE_RETENTION_HOURS = int(os.environ.get('FILE_RETENTION_HOURS', 24))

    DEBUG_MODE = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    GLOBAL_LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
    GLOBAL_LOG_FILE = os.environ.get('GLOBAL_LOG_FILE', 'unity_extractor_global.log')
    SESSION_LOGS_DIR = 'logs/sessions'
    SESSION_LOG_LEVEL = 'DEBUG'  # Detailed logging for individual sessions

    SECRET_KEY = os.environ.get('SECRET_KEY', 'default-dev-secret-key-change-in-production')

    # Rate Limiting Configuration for /api/upload endpoint
    RATE_LIMIT_ENABLED = os.environ.get('RATE_LIMIT_ENABLED', 'True').lower() == 'true'
    RATE_LIMIT_PER_MINUTE = int(os.environ.get('RATE_LIMIT_PER_MINUTE', 10)) # Max requests per minute
    RATE_LIMIT_WINDOW_SECONDS = 60 # Window for rate limit, default 60 seconds (1 minute)

    # Worker Pool Configuration
    WEB_CONCURRENCY = int(os.environ.get('WEB_CONCURRENCY', 2)) # Number of internal worker threads for queue processing