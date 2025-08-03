# -*- coding: utf-8 -*-
"""
UnityBundleExtractor - Asset Inventory Builder Module
Author: lenzarchive (https://github.com/lenzarchive)
License: MIT License

This module provides a standalone function for building a structured inventory
of assets found within a Unity environment, including estimated export sizes.
"""

import json
import logging
import io
from collections import defaultdict
from typing import Dict, List, Any
import UnityPy
from PIL import Image

from ._object_namer import get_object_name

def build_asset_inventory(objects: List[Any], local_logger: logging.Logger, debug_mode: bool) -> Dict[str, List[Dict]]:
    """
    Iterates through all objects loaded from the bundle and creates a structured,
    categorized dictionary of asset information. For each asset, it includes
    a simulated estimated size, name, type, and internal index.

    Args:
        objects (List[Any]): A list of UnityPy ObjectReader objects from the environment.
        local_logger (logging.Logger): The logger instance for recording messages.
        debug_mode (bool): Flag indicating if the application is in debug mode.

    Returns:
        Dict[str, List[Dict]]: A dictionary where keys are asset types (categories)
                               and values are lists of asset information dictionaries.
    """
    asset_categories = defaultdict(list)
    
    # Default options for simulating export size calculation
    default_export_options = {
        'image_format': 'png',
        'audio_format': 'wav',
        'font_format': 'ttf'
    }

    for i, obj in enumerate(objects):
        try:
            obj_type_name = obj.type.name
            obj_size = 0

            try:
                data = obj.read()
                temp_buffer = io.BytesIO()
                
                if obj_type_name in ["Texture2D", "Sprite"]:
                    if hasattr(data, 'image') and data.image:
                        img_format = default_export_options['image_format'].upper()
                        if img_format == 'JPEG': img_format = 'JPG'
                        img = data.image
                        if img_format == 'JPG' and img.mode == 'RGBA':
                            img = img.convert('RGB')
                        img.save(temp_buffer, format=img_format)
                
                elif obj_type_name == "AudioClip":
                    if hasattr(data, "m_AudioData") and data.m_AudioData:
                        temp_buffer.write(data.m_AudioData)

                elif obj_type_name == "Font":
                    if hasattr(data, "m_FontData") and data.m_FontData:
                        temp_buffer.write(data.m_FontData)

                elif obj_type_name == "Mesh":
                    if hasattr(data, 'export'):
                        obj_data = data.export().encode('utf-8')
                        temp_buffer.write(obj_data)

                elif obj_type_name in ["Shader", "TextAsset", "MonoScript"]:
                     if hasattr(data, 'm_Script') and isinstance(data.m_Script, (bytes, str)):
                        script_data = data.m_Script.encode('utf-8', errors='replace') if isinstance(data.m_Script, str) else data.m_Script
                        temp_buffer.write(script_data)

                elif obj_type_name in ["MovieTexture", "VideoClip"]:
                    if hasattr(data, "m_MovieData") and data.m_MovieData:
                        temp_buffer.write(data.m_MovieData)

                else:
                    try:
                        typetree_json = json.dumps(data.read_typetree(), indent=2, ensure_ascii=False, default=str).encode('utf-8', errors='replace')
                        temp_buffer.write(typetree_json)
                    except Exception:
                        local_logger.debug(f"Could not read typetree for {obj.path_id} ({obj_type_name}) for size estimation.")
                        obj_size = obj.data_size
                obj_size = temp_buffer.tell()
                temp_buffer.close()
            
            except Exception as size_e:
                local_logger.debug(f"Could not accurately estimate export size for object {obj.path_id} ({obj_type_name}): {size_e}", exc_info=debug_mode)
                obj_size = obj.data_size
            
            asset_info = {
                'index': i,
                'path_id': str(obj.path_id),
                'name': get_object_name(obj),
                'type': obj_type_name,
                'estimated_size': obj_size,
                'class_id': obj.type.value if hasattr(obj.type, 'value') else 0
            }
            asset_categories[obj_type_name].append(asset_info)
        except Exception as e:
            local_logger.error(f"Error processing object {i} (PathID: {obj.path_id}) for inventory: {e}", exc_info=debug_mode)
    return dict(asset_categories)