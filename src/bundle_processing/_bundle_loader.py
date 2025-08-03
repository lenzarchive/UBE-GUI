# -*- coding: utf-8 -*-
"""
UnityBundleExtractor - Bundle Loader Module
Author: lenzarchive (https://github.com/lenzarchive)
License: MIT License

This module provides standalone functions for loading Unity environments
and extracting basic bundle information.
"""

import logging
import os
import UnityPy

from src.utils import get_file_info

def load_unity_environment(bundle_path: str, local_logger: logging.Logger) -> UnityPy.Environment:
    """
    Loads a Unity asset bundle or asset file into a UnityPy Environment.

    Args:
        bundle_path (str): The file system path to the bundle or asset file.
        local_logger (logging.Logger): The logger instance for recording messages.

    Returns:
        UnityPy.Environment: The loaded UnityPy Environment object.

    Raises:
        Exception: If UnityPy fails to load the environment.
    """
    local_logger.debug(f"Attempting to load UnityPy environment from {bundle_path}")
    env = UnityPy.load(bundle_path)
    local_logger.debug("UnityPy environment loaded successfully.")
    return env

def get_bundle_info(bundle_path: str, local_logger: logging.Logger) -> dict:
    """
    Retrieves basic information about a bundle file, such as size, signature, and compression type.

    Args:
        bundle_path (str): The file system path to the bundle or asset file.
        local_logger (logging.Logger): The logger instance for recording messages.

    Returns:
        dict: A dictionary containing 'signature', 'size', 'compression', and 'version_header_guess'.
    """
    return get_file_info(bundle_path)