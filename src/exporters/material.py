# -*- coding: utf-8 -*-
"""
UnityBundleExtractor - Material Exporter Module
Author: lenzarchive (https://github.com/lenzarchive)
License: MIT License

This module provides a standalone function for exporting Unity Material assets.
"""

import json
import logging
from typing import Any

# Configure logger for this module
logger = logging.getLogger(__name__)

def export_material(data: Any, output_path: str, debug_mode: bool, local_logger: logging.Logger) -> bool:
    """
    Exports Material properties (colors, textures, floats) to a JSON file.

    Args:
        data (Any): The UnityPy object data for the material.
        output_path (str): The base path for the output file (without extension).
        debug_mode (bool): Flag indicating if the application is in debug mode.
        local_logger (logging.Logger): The logger instance for recording messages.

    Returns:
        bool: True if the material was successfully exported, False otherwise.
    """
    try:
        local_logger.debug(f"Attempting to export Material: {output_path}")
        material_info = {
            'name': getattr(data, 'm_Name', 'Unknown'),
            'shader_path_id': str(getattr(getattr(data, 'm_Shader', None), 'path_id', 0)) if hasattr(data, 'm_Shader') else '0',
            'properties': {}
        }
        if hasattr(data, 'm_SavedProperties'):
            props = data.m_SavedProperties
            
            # Texture properties
            if hasattr(props, 'm_TexEnvs'):
                material_info['properties']['textures'] = {
                    tex.first: {'texture_path_id': str(getattr(getattr(tex.second, 'm_Texture', None), 'path_id', 0)) if hasattr(tex.second, 'm_Texture') else '0'}
                    for tex in props.m_TexEnvs if hasattr(tex, 'first')
                }
            # Float properties
            if hasattr(props, 'm_Floats'):
                material_info['properties']['floats'] = {
                    f.first: f.second for f in props.m_Floats if hasattr(f, 'first')
                }
            # Color properties
            if hasattr(props, 'm_Colors'):
                material_info['properties']['colors'] = {
                    c.first: {'r': c.second.r, 'g': c.second.g, 'b': c.second.b, 'a': c.second.a}
                    for c in props.m_Colors if hasattr(c, 'first')
                }
        
        with open(f"{output_path}.mat.json", 'w', encoding='utf-8') as f:
            json.dump(material_info, f, indent=2, ensure_ascii=False)
        
        local_logger.debug(f"Material {output_path} saved.")
        return True
    except Exception as e:
        local_logger.error(f"Material export failed for {output_path}: {e}", exc_info=debug_mode)
        return False