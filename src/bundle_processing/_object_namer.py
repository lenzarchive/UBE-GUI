# -*- coding: utf-8 -*-
"""
UnityBundleExtractor - Object Namer Module
Author: lenzarchive (https://github.com/lenzarchive)
License: MIT License

This module provides a standalone function to retrieve a descriptive name
for a Unity object, utilizing naming conventions found in Unity projects.
"""

import logging
from typing import Any
import UnityPy # For UnityPy.files.ObjectReader type hint

from src.utils import sanitize_filename # Import utility function

# Configure logger for this module
logger = logging.getLogger(__name__)

def get_object_name(obj: Any) -> str:
    """
    Retrieves a descriptive name for a Unity object by checking various
    attributes within its data. It also sanitizes the name for safe file system use.

    Args:
        obj (Any): The UnityPy object instance (ObjectReader or Asset).

    Returns:
        str: A sanitized, descriptive name for the object.
    """
    # If the input is already a string, sanitize and return it
    if isinstance(obj, str):
        return sanitize_filename(obj)

    try:
        # Read the object's data to access its attributes
        data = obj.read()
        
        # Check common name attributes within the object's data
        name_attributes = ["m_Name", "name"]
        for attr in name_attributes:
            if hasattr(data, attr) and getattr(data, attr):
                return sanitize_filename(getattr(data, attr))

        # Special handling for MonoBehaviour to get name from associated GameObject
        if hasattr(data, 'm_GameObject') and getattr(data, 'm_GameObject') and getattr(data.m_GameObject, 'path_id', 0) != 0:
            try:
                game_object = data.m_GameObject.read()
                if hasattr(game_object, 'm_Name') and game_object.m_Name:
                    return sanitize_filename(f"{game_object.m_Name}_{obj.type.name}")
            except Exception:
                # Silently pass on read errors for linked objects, as per original project's behavior
                pass
        
        # Special handling for MonoScript to get its class name
        if obj.type.name == "MonoScript" and hasattr(data, "m_ClassName") and data.m_ClassName:
            return sanitize_filename(data.m_ClassName)
            
        # Special handling for MonoBehaviour to get class name from associated MonoScript
        if obj.type.name == "MonoBehaviour" and hasattr(data, 'm_Script') and getattr(data, 'm_Script') and getattr(data.m_Script, 'path_id', 0) != 0:
            try:
                script = data.m_Script.read()
                if hasattr(script, 'm_ClassName') and script.m_ClassName:
                     return sanitize_filename(script.m_ClassName)
            except Exception:
                # Silently pass on read errors for linked scripts, as per original project's behavior
                pass

    except Exception as e:
        # Log a warning if the object data itself cannot be read for naming purposes
        logger.warning(f"Could not fully read object {obj.path_id} for naming: {e}")

    # Fallback: If no descriptive name is found after all attempts, use type and path_id
    return f"{obj.type.name}_{obj.path_id}"