# -*- coding: utf-8 -*-
"""
UnityBundleExtractor - Video Exporter Module
Author: lenzarchive (https://github.com/lenzarchive)
License: MIT License

This module provides a standalone function for exporting Unity VideoClip or MovieTexture assets.
"""

import os
import json
import logging
from typing import Any

# Configure logger for this module
logger = logging.getLogger(__name__)

def _detect_video_format(video_data: bytes) -> str:
    """
    Detects common video file formats from their binary data headers.
    """
    if len(video_data) < 8: return '.video'
    header = video_data[:8]
    if header[4:8] == b'ftyp': return '.mp4'
    if header[:4] == b'RIFF' and len(video_data) >= 12 and video_data[8:12] == b'WAVE': return '.wav'
    if header[:3] == b'FLV': return '.flv'
    if header[:2] == b'\x1a\x45': return '.mkv'
    return '.mov'
        
def export_video(data: Any, output_path: str, debug_mode: bool, local_logger: logging.Logger) -> bool:
    """
    Exports a VideoClip or MovieTexture asset to a video file.
    Attempts to detect the video format based on its header.

    Args:
        data (Any): The UnityPy object data for the video clip.
        output_path (str): The base path for the output file (without extension).
        debug_mode (bool): Flag indicating if the application is in debug mode.
        local_logger (logging.Logger): The logger instance for recording messages.

    Returns:
        bool: True if the video clip was successfully exported, False otherwise.
    """
    try:
        local_logger.debug(f"Attempting to export VideoClip: {output_path}")
        video_data = getattr(data, 'm_MovieData', None)
        if not video_data:
            local_logger.debug(f"VideoClip {output_path} has no video data, skipping.")
            return False
        
        ext = _detect_video_format(video_data)
        with open(f"{output_path}{ext}", 'wb') as f:
            f.write(video_data)

        local_logger.debug(f"VideoClip {output_path} saved as {ext}.")
        return True
    except Exception as e:
        local_logger.error(f"Video export failed for {output_path}: {e}", exc_info=debug_mode)
        return False