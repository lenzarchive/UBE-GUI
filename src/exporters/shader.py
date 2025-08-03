# -*- coding: utf-8 -*-
"""
UnityBundleExtractor - Shader Exporter Module
Author: lenzarchive (https://github.com/lenzarchive)
License: MIT License

This module provides a standalone function for exporting Unity Shader assets.
"""

import json
import logging
from typing import Any

# Configure logger for this module
logger = logging.getLogger(__name__)

def _extract_shader_properties(data: Any) -> list:
    """
    Helper function to extract properties from a parsed shader form.
    """
    properties = []
    try:
        if hasattr(data, 'm_ParsedForm') and hasattr(data.m_ParsedForm, 'm_PropInfo'):
            prop_info = data.m_ParsedForm.m_PropInfo
            if hasattr(prop_info, 'm_Props'):
                for prop in prop_info.m_Props:
                    properties.append({
                        'name': getattr(prop, 'm_Name', ''),
                        'description': getattr(prop, 'm_Description', ''),
                        'type': str(getattr(prop, 'm_Type', 'Unknown'))
                    })
    except Exception as e:
        logger.warning(f"Failed to extract shader properties: {e}")
    return properties
    
def export_shader(data: Any, output_path: str, debug_mode: bool, local_logger: logging.Logger) -> bool:
    """
    Exports a Shader asset to a .shader source file. Also generates a metadata JSON.

    Args:
        data (Any): The UnityPy object data for the shader.
        output_path (str): The base path for the output file (without extension).
        debug_mode (bool): Flag indicating if the application is in debug mode.
        local_logger (logging.Logger): The logger instance for recording messages.

    Returns:
        bool: True if the shader was successfully exported, False otherwise.
    """
    try:
        local_logger.debug(f"Attempting to export Shader: {output_path}")
        shader_content = getattr(data, 'm_Script', '')
        if not shader_content:
            local_logger.debug(f"Shader {output_path} has no script content, skipping.")
            return False
        
        with open(f"{output_path}.shader", 'w', encoding='utf-8', errors='replace') as f:
            f.write(shader_content)
            
        metadata = {
            'name': getattr(data, 'm_Name', 'Unknown'),
            'properties': _extract_shader_properties(data)
        }
        with open(f"{output_path}_meta.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        local_logger.debug(f"Shader {output_path} saved.")
        return True
    except Exception as e:
        local_logger.error(f"Shader export failed for {output_path}: {e}", exc_info=debug_mode)
        return False