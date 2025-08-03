# -*- coding: utf-8 -*-
"""
UnityBundleExtractor - Font Exporter Module
Author: lenzarchive (https://github.com/lenzarchive)
License: MIT License

This module provides a standalone function for exporting Unity Font assets.
"""

import os
import json
import logging
from typing import Any

# Configure logger for this module
logger = logging.getLogger(__name__)

def export_font(data: Any, output_path: str, debug_mode: bool, local_logger: logging.Logger) -> bool:
    """
    Exports a Font asset to a .ttf or .otf file based on detected font header.

    Args:
        data (Any): The UnityPy object data for the font.
        output_path (str): The base path for the output file (without extension).
        debug_mode (bool): Flag indicating if the application is in debug mode.
        local_logger (logging.Logger): The logger instance for recording messages.

    Returns:
        bool: True if the font was successfully exported, False otherwise.
    """
    try:
        local_logger.debug(f"Attempting to export Font: {output_path}")
        if not hasattr(data, 'm_FontData') or not data.m_FontData:
            local_logger.debug(f"Font {output_path} has no font data, skipping.")
            return False
        
        font_data = data.m_FontData
        header = font_data[:4]
        ext = '.font'
        if header == b'OTTO': ext = '.otf'
        elif header in [b'\x00\x01\x00\x00', b'true']: ext = '.ttf'
        
        with open(f"{output_path}{ext}", 'wb') as f:
            f.write(font_data)

        # Save font metadata
        metadata = {
            'format': ext[1:],
            'size_bytes': len(font_data),
            'font_name': getattr(data, 'm_Name', 'Unknown'),
        }
        with open(f"{output_path}_meta.json", 'w') as f:
            json.dump(metadata, f, indent=2)

        local_logger.debug(f"Font {output_path} saved as {ext}.")
        return True
    except Exception as e:
        local_logger.error(f"Font export failed for {output_path}: {e}", exc_info=debug_mode)
        return False