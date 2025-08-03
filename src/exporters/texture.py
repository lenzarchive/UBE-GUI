# -*- coding: utf-8 -*-
"""
UnityBundleExtractor - Texture Exporter Module
Author: lenzarchive (https://github.com/lenzarchive)
License: MIT License

This module provides a standalone function for exporting Unity Texture2D and Sprite assets.
"""

import json
import os
import logging
import io
from typing import Any

from PIL import Image

# Configure logger for this module
logger = logging.getLogger(__name__)

def _save_texture_metadata(data: Any, output_path: str, exported_format: str, local_logger: logging.Logger):
    """
    Saves a JSON metadata file for an exported texture.
    """
    metadata = {
        'width': getattr(data, 'm_Width', 'Unknown'),
        'height': getattr(data, 'm_Height', 'Unknown'),
        'format_unity': str(getattr(data, 'm_Format', 'Unknown')),
        'exported_format': exported_format,
        'filter_mode': str(getattr(data, 'm_FilterMode', 'Unknown')),
        'wrap_mode': str(getattr(data, 'm_WrapMode', 'Unknown')),
        'mip_count': getattr(data, 'm_MipCount', 1),
        'readable': getattr(data, 'm_IsReadable', False)
    }
    try:
        with open(f"{output_path}_meta.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)
        local_logger.debug(f"Saved metadata for texture: {output_path}")
    except Exception as e:
        local_logger.warning(f"Failed to save metadata for {output_path}: {e}")

def export_texture(data: Any, output_path: str, debug_mode: bool, local_logger: logging.Logger) -> bool:
    """
    Exports a Texture2D or Sprite asset to an image file (PNG or JPG).
    Prioritizes JPG for non-transparent images to save space, falls back to PNG.

    Args:
        data (Any): The UnityPy object data for the texture/sprite.
        output_path (str): The base path for the output file (without extension).
        debug_mode (bool): Flag indicating if the application is in debug mode.
        local_logger (logging.Logger): The logger instance for recording messages.

    Returns:
        bool: True if the texture was successfully exported, False otherwise.
    """
    try:
        local_logger.debug(f"Attempting to export Texture2D/Sprite: {output_path}")
        
        if hasattr(data, 'image') and data.image:
            img = data.image
            exported_format_ext = 'png'
            
            if img.mode in ('RGB', 'L') or (img.mode == 'RGBA' and img.getextrema()[3][0] == 255):
                try:
                    output_file_jpg = f"{output_path}.jpg"
                    img.save(output_file_jpg, optimize=True, quality=90)
                    _save_texture_metadata(data, output_path, 'jpg', local_logger)
                    local_logger.debug(f"Texture {output_path} saved as JPG.")
                    return True
                except Exception as jpg_e:
                    local_logger.warning(f"Failed to save {output_path} as JPG, falling back to PNG. Error: {jpg_e}", exc_info=debug_mode)
            
            output_file_png = f"{output_path}.png"
            img.save(output_file_png, optimize=True)
            _save_texture_metadata(data, output_path, exported_format_ext, local_logger)
            local_logger.debug(f"Texture {output_path} saved as PNG.")
            return True

        elif hasattr(data, 'm_StreamData') and data.m_StreamData:
            with open(f"{output_path}.raw", 'wb') as f:
                f.write(data.m_StreamData)
            _save_texture_metadata(data, output_path, 'raw_stream', local_logger)
            local_logger.warning(f"Texture for {output_path} saved as raw stream. Associated .resS file might be missing.")
            return True

        elif hasattr(data, 'image_data') and data.image_data:
            with open(f"{output_path}.raw_imgdata", 'wb') as f:
                f.write(data.image_data)
            _save_texture_metadata(data, output_path, 'raw_imagedata', local_logger)
            local_logger.warning(f"Texture for {output_path} saved as raw image data. Associated .resS file might be missing.")
            return True
        
        local_logger.warning(f"Texture export skipped: No usable image or raw data found for {output_path}.")
        return False
        
    except Exception as e:
        local_logger.error(f"Texture export failed for {output_path}: {e}", exc_info=debug_mode)
        return False