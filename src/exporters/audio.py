# -*- coding: utf-8 -*-
"""
UnityBundleExtractor - Audio Exporter Module
Author: lenzarchive (https://github.com/lenzarchive)
License: MIT License

This module provides a standalone function for exporting Unity AudioClip assets.
"""

import os
import json
import logging
from typing import Any

# Configure logger for this module
logger = logging.getLogger(__name__)

def _detect_audio_format(audio_data: bytes) -> str:
    """
    Detects common audio file formats from their binary data headers.

    Args:
        audio_data (bytes): The initial bytes of the audio data.

    Returns:
        str: The detected file extension (e.g., 'ogg', 'wav', 'mp3') or 'unknown'.
    """
    if len(audio_data) < 4: return 'unknown'
    header = audio_data[:4]
    if header == b'OggS': return 'ogg'
    if header[:4] == b'RIFF' and len(audio_data) >= 12 and audio_data[8:12] == b'WAVE': return 'wav'
    if header == b'fLaC': return 'flac'
    if audio_data.startswith(b'ID3') or audio_data[0:2] == b'\xff\xfb' or audio_data[0:2] == b'\xff\xf3': return 'mp3'
    return 'unknown'

def export_audio(data: Any, output_path: str, debug_mode: bool, local_logger: logging.Logger) -> bool:
    """
    Exports an AudioClip asset to its native audio file format based on detected header.

    Args:
        data (Any): The UnityPy object data for the audio clip.
        output_path (str): The base path for the output file (without extension).
        debug_mode (bool): Flag indicating if the application is in debug mode.
        local_logger (logging.Logger): The logger instance for recording messages.

    Returns:
        bool: True if the audio clip was successfully exported, False otherwise.
    """
    try:
        local_logger.debug(f"Attempting to export AudioClip: {output_path}")
        if not hasattr(data, 'm_AudioData') or not data.m_AudioData:
            local_logger.debug(f"AudioClip {output_path} has no audio data, skipping.")
            return False
        
        audio_data = data.m_AudioData
        audio_format = _detect_audio_format(audio_data)
        ext = f".{audio_format}" if audio_format != 'unknown' else '.audio'
        
        with open(f"{output_path}{ext}", 'wb') as f:
            f.write(audio_data)
            
        # Save audio metadata
        metadata = {
            'format': audio_format,
            'size_bytes': len(audio_data),
            'channels': getattr(data, 'm_Channels', 0),
            'frequency': getattr(data, 'm_Frequency', 0),
            'length_seconds': getattr(data, 'm_Length', 0.0),
            'compression': str(getattr(data, 'm_CompressionFormat', 'Unknown'))
        }
        with open(f"{output_path}_meta.json", 'w') as f:
            json.dump(metadata, f, indent=2)

        local_logger.debug(f"AudioClip {output_path} saved as {ext}.")
        return True
    except Exception as e:
        local_logger.error(f"Audio export failed for {output_path}: {e}", exc_info=debug_mode)
        return False