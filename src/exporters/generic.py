# -*- coding: utf-8 -*-
"""
UnityBundleExtractor - Generic Exporter Module
Author: lenzarchive (https://github.com/lenzarchive)
License: MIT License

This module provides a standalone function for exporting generic Unity objects
or those not handled by specific exporters, typically as a JSON representation
of their internal structure (TypeTree).
"""

import json
import logging
from typing import Any

# Configure logger for this module
logger = logging.getLogger(__name__)

def _serialize_object(data: Any) -> Any:
    """
    A recursive helper function to serialize complex Unity objects into a JSON-friendly format.
    Handles nested objects, lists, and UnityPy's PPtr (Pointer) objects.
    """
    if data is None: return None
    if isinstance(data, (str, int, float, bool)): return data
    if isinstance(data, bytes):
        try:
            return data.decode('utf-8', errors='replace')
        except Exception:
            return f"<binary data: {len(data)} bytes>"
    if isinstance(data, (list, tuple)):
        return [_serialize_object(item) for item in data]
    if isinstance(data, dict):
        return {key: _serialize_object(value) for key, value in data.items()}
    
    if hasattr(data, 'path_id'):
        if hasattr(data, 'file_id'):
            return {
                'type': 'ObjectReference',
                'file_id': getattr(data, 'file_id', 0),
                'path_id': str(data.path_id)
            }
        else:
            return {'type': 'ObjectReference', 'path_id': str(data.path_id)}

    if hasattr(data, '__dict__'):
        return {
            key: _serialize_object(value)
            for key, value in data.__dict__.items()
            if not key.startswith('_')
        }
    try:
        return str(data)
    except Exception:
        return 'Unserializable Object'

def export_generic(data: Any, output_path: str, obj_type: str, debug_mode: bool, local_logger: logging.Logger) -> bool:
    """
    A generic exporter for any Unity object type not handled by specific methods.
    It attempts to read the object's TypeTree and saves it as a JSON file,
    providing a raw dump of its internal structure.

    Args:
        data (Any): The UnityPy object data.
        output_path (str): The base path for the output file (without extension).
        obj_type (str): The name of the Unity object type (e.g., "GameObject", "MonoBehaviour").
        debug_mode (bool): Flag indicating if the application is in debug mode.
        local_logger (logging.Logger): The logger instance for recording messages.

    Returns:
        bool: True if the generic object was successfully exported, False otherwise.
    """
    try:
        local_logger.debug(f"Exporting generic object '{obj_type}': {output_path}")
        
        try:
            type_tree_data = data.read_typetree()
        except Exception as e:
            local_logger.debug(f"Failed to read typetree for {output_path} ({obj_type}), falling back to generic serialization: {e}")
            type_tree_data = _serialize_object(data)
        
        if not type_tree_data:
            local_logger.debug(f"Object {output_path} ({obj_type}) has no data to export, skipping.")
            return False
        
        with open(f"{output_path}.json", 'w', encoding='utf-8') as f:
            json.dump(type_tree_data, f, indent=2, ensure_ascii=False, default=str)
        
        local_logger.debug(f"Generic object {output_path} ({obj_type}) saved as JSON.")
        return True
    except Exception as e:
        local_logger.error(f"Generic export failed for {output_path} ({obj_type}): {e}", exc_info=debug_mode)
        return False