# -*- coding: utf-8 -*-
"""
UnityBundleExtractor - MonoScript Exporter Module
Author: lenzarchive (https://github.com/lenzarchive)
License: MIT License

This module provides a standalone function for exporting Unity MonoScript assets.
"""

import json
import logging
from typing import Any
from .generic import export_generic

# Configure logger for this module
logger = logging.getLogger(__name__)

def export_mono_script(data: Any, output_path: str, debug_mode: bool, local_logger: logging.Logger) -> bool:
    """
    Exports a MonoScript asset to a .cs file if its source code is available.
    If not, it falls back to a generic JSON export of its TypeTree.

    Args:
        data (Any): The UnityPy object data for the MonoScript.
        output_path (str): The base path for the output file (without extension).
        debug_mode (bool): Flag indicating if the application is in debug mode.
        local_logger (logging.Logger): The logger instance for recording messages.

    Returns:
        bool: True if the mono script was successfully exported, False otherwise.
    """
    try:
        local_logger.debug(f"Attempting to export MonoScript: {output_path}")
        # The actual C# source (m_Script) is often not embedded in bundles for MonoScript.
        # It's usually a reference.
        script_content = getattr(data, 'm_Script', '')
        if isinstance(script_content, bytes):
            script_content = ''

        if not script_content or not script_content.strip():
            # If source is not directly available, fall back to generic exporter
            local_logger.debug(f"MonoScript {output_path} has no script content, falling back to generic export.")
            return export_generic(data, output_path, "MonoScript", debug_mode, local_logger)

        with open(f"{output_path}.cs", 'w', encoding='utf-8') as f:
            f.write(script_content)

        metadata = {
                'class_name': getattr(data, 'm_ClassName', ''),
                'namespace': getattr(data, 'm_Namespace', ''),
                'assembly_name': getattr(data, 'm_AssemblyName', '')
            }
        with open(f"{output_path}_meta.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        local_logger.debug(f"MonoScript {output_path} saved as .cs.")
        return True
    except Exception as e:
        local_logger.error(f"MonoScript export failed for {output_path}: {e}", exc_info=debug_mode)
        return False