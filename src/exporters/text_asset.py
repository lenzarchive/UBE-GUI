# -*- coding: utf-8 -*-
"""
UnityBundleExtractor - TextAsset Exporter Module
Author: lenzarchive (https://github.com/lenzarchive)
License: MIT License

This module provides a standalone function for exporting Unity TextAsset objects.
"""

import os
import json
import logging
from typing import Any

# Configure logger for this module
logger = logging.getLogger(__name__)

def _detect_text_format(content: str) -> str:
    """
    Detects if text content is likely JSON, XML, or YAML based on its structure.
    """
    content_stripped = content.strip()
    if content_stripped.startswith(('{', '[')): return '.json'
    if content_stripped.startswith('<?xml'): return '.xml'
    if content_stripped.startswith('---'): return '.yaml'
    return '.txt'

def export_text_asset(data: Any, output_path: str, debug_mode: bool, local_logger: logging.Logger) -> bool:
    """
    Exports a TextAsset to a file, attempting to detect its format (JSON, XML, YAML, or plain text).

    Args:
        data (Any): The UnityPy object data for the text asset.
        output_path (str): The base path for the output file (without extension).
        debug_mode (bool): Flag indicating if the application is in debug mode.
        local_logger (logging.Logger): The logger instance for recording messages.

    Returns:
        bool: True if the text asset was successfully exported, False otherwise.
    """
    try:
        local_logger.debug(f"Attempting to export TextAsset: {output_path}")
        if not hasattr(data, 'm_Script'):
            local_logger.debug(f"TextAsset {output_path} has no script content, skipping.")
            return False
        
        content = data.m_Script
        if isinstance(content, bytes):
            content = content.decode('utf-8', errors='replace')
        
        if not content.strip(): 
            local_logger.debug(f"TextAsset {output_path} has empty content, skipping.")
            return False
        
        ext = _detect_text_format(content)
        
        with open(f"{output_path}{ext}", 'w', encoding='utf-8') as f:
            f.write(content)

        local_logger.debug(f"TextAsset {output_path} saved as {ext}.")
        return True
    except Exception as e:
        local_logger.error(f"TextAsset export failed for {output_path}: {e}", exc_info=debug_mode)
        return False