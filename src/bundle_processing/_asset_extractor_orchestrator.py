# -*- coding: utf-8 -*-
"""
UnityBundleExtractor - Asset Extractor Orchestrator Module
Author: lenzarchive (https://github.com/lenzarchive)
License: MIT License

This module provides a standalone function to orchestrate the extraction of a single
Unity asset object by routing it to the appropriate specialized exporter function.
"""

import logging
import os
from typing import Any
import traceback

# Import individual exporter functions
from src.exporters.audio import export_audio
from src.exporters.font import export_font
from src.exporters.generic import export_generic
from src.exporters.material import export_material
from src.exporters.mesh import export_mesh_obj
from src.exporters.mono_script import export_mono_script
from src.exporters.shader import export_shader
from src.exporters.text_asset import export_text_asset
from src.exporters.texture import export_texture
from src.exporters.video import export_video

from ._object_namer import get_object_name

def extract_single_asset_orchestrator(obj: Any, base_dir: str, local_logger: logging.Logger, debug_mode: bool) -> bool:
    """
    Orchestrates the extraction of a single Unity asset object.
    It routes the object to the appropriate specialized exporter function based on its type.

    Args:
        obj (Any): The UnityPy object to extract.
        base_dir (str): The base directory where the extracted asset should be saved.
        local_logger (logging.Logger): The logger instance for recording messages.
        debug_mode (bool): Flag indicating if the application is in debug mode.

    Returns:
        bool: True if the asset was successfully extracted, False otherwise.
    """
    obj_type = obj.type.name
    obj_name = get_object_name(obj)
    
    # Create a subdirectory for the asset type within the base output directory
    type_dir = os.path.join(base_dir, get_object_name(obj_type))
    os.makedirs(type_dir, exist_ok=True)
    output_path = os.path.join(type_dir, obj_name)
    
    success = False
    try:
        data = obj.read()
        
        # Explicitly map UnityPy object types to their dedicated exporter functions
        if obj_type in ["Texture2D", "Sprite"]:
            success = export_texture(data, output_path, debug_mode, local_logger)
        elif obj_type == "Mesh":
            success = export_mesh_obj(data, output_path, debug_mode, local_logger)
        elif obj_type == "AudioClip":
            success = export_audio(data, output_path, debug_mode, local_logger)
        elif obj_type == "Font":
            success = export_font(data, output_path, debug_mode, local_logger)
        elif obj_type == "Shader":
            success = export_shader(data, output_path, debug_mode, local_logger)
        elif obj_type == "TextAsset":
            success = export_text_asset(data, output_path, debug_mode, local_logger)
        elif obj_type == "MonoScript":
            success = export_mono_script(data, output_path, debug_mode, local_logger)
        elif obj_type == "Material":
            success = export_material(data, output_path, debug_mode, local_logger)
        elif obj_type in ["VideoClip", "MovieTexture"]:
            success = export_video(data, output_path, debug_mode, local_logger)
        else:
            # Fallback to generic exporter for any unhandled or unknown types
            success = export_generic(data, output_path, obj_type, debug_mode, local_logger)

        if not success:
            local_logger.warning(f"Exporter returned False for {obj_type} object: {obj_name}. No specific file format was saved.")
            
    except Exception as e:
        local_logger.error(f"Failed to extract asset '{obj_name}' (Type: {obj_type}, PathID: {obj.path_id}): {e}", exc_info=debug_mode)
        success = False

    return success