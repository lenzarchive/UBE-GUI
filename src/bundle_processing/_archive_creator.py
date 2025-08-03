# -*- coding: utf-8 -*-
"""
UnityBundleExtractor - Archive Creator Module
Author: lenzarchive (https://github.com/lenzarchive)
License: MIT License

This module provides a standalone function to create a ZIP archive
from a directory containing extracted Unity assets.
"""

import os
import zipfile
import logging
from src.utils import sanitize_filename

def create_archive(source_dir: str, original_bundle_name: str, output_folder: str, session_id: str, local_logger: logging.Logger) -> str:
    """
    Creates a ZIP archive from the contents of a source directory.
    The ZIP file is named based on the original bundle file, with a fallback to session ID.

    Args:
        source_dir (str): The directory containing files to be zipped.
        original_bundle_name (str): The original filename of the uploaded bundle, used for naming the ZIP.
        output_folder (str): The base directory where the ZIP archive will be saved.
        session_id (str): The unique identifier for the current session.
        local_logger (logging.Logger): The logger instance for recording messages.

    Returns:
        str: The full path to the created ZIP archive.
    """
    base_name = os.path.splitext(original_bundle_name)[0]
    sanitized_base_name = sanitize_filename(base_name)
    
    if sanitized_base_name and sanitized_base_name != "Untitled":
         zip_filename = f"{sanitized_base_name}_extracted.zip" 
    else:
         zip_filename = f"unity_assets_{session_id}.zip"

    zip_path = os.path.join(output_folder, zip_filename)
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(source_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arc_path = os.path.relpath(file_path, source_dir)
                zipf.write(file_path, arc_path)
    local_logger.info(f"Created ZIP archive: {zip_path}")
    return zip_path