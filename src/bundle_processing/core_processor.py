# -*- coding: utf-8 -*-
"""
UnityBundleExtractor - Core Bundle Processor Module
Author: lenzarchive (https://github.com/lenzarchive)
License: MIT License

This module defines the main BundleProcessor class, which orchestrates
the various stages of Unity asset bundle processing, including analysis
and extraction, by delegating tasks to highly specialized functions.
"""

import os
import shutil
import logging
from datetime import datetime
from collections import defaultdict
import tempfile
from typing import Dict, List, Any
import traceback
import threading # For _is_cancelled flag (Event is overkill, bool is fine)

# Import individual processing functions
from ._bundle_loader import load_unity_environment, get_bundle_info
from ._object_namer import get_object_name
from ._asset_inventory_builder import build_asset_inventory
from ._asset_extractor_orchestrator import extract_single_asset_orchestrator
from ._archive_creator import create_archive
from src.session.logger_setup import setup_session_logger

class BundleProcessor:
    """
    Manages the entire lifecycle of a session for a given Unity bundle file,
    from initial analysis to asset extraction and temporary file cleanup.
    It orchestrates operations by calling specialized functions from other modules.
    """
    def __init__(self, session_id: str, bundle_path: str, original_filename: str, session_upload_dir: str, app_config: Dict):
        """
        Initializes a new BundleProcessor session.

        Args:
            session_id (str): A unique identifier for the session.
            bundle_path (str): The file system path to the primary Unity bundle file.
            original_filename (str): The original filename of the uploaded bundle.
            session_upload_dir (str): The directory where all session-related uploaded files are stored.
            app_config (Dict): The application's configuration dictionary.
        """
        self.session_id = session_id
        self.bundle_path = bundle_path
        self.original_filename = original_filename
        self.session_upload_dir = session_upload_dir
        self.output_dir = None
        self.env = None
        self.objects = []
        self.metadata = {}
        self.processing_status = "initializing"
        self.error_message = None
        self.progress = 0
        self.app_config = app_config
        self._is_cancelled = False # Flag to indicate if the task has been requested to be cancelled
        
        self.logger = setup_session_logger(session_id, app_config['SESSION_LOGS_DIR'], app_config['SESSION_LOG_LEVEL'])
        self.export_stats = {'success': 0, 'failed': 0, 'skipped': 0}

    def _check_cancellation(self):
        """Raises an exception if the task has been cancelled."""
        if self._is_cancelled:
            self.logger.info(f"Processing for session {self.session_id} cancelled.")
            self.processing_status = "cancelled"
            self.error_message = "Task cancelled by user."
            # Perform immediate cleanup if cancelled during processing
            self.cleanup() 
            raise InterruptedError("Task cancelled by user.")

    def analyze_bundle(self):
        """
        Orchestrates the analysis of the Unity bundle.
        It loads the bundle, builds an inventory of its assets, and generates comprehensive metadata.
        """
        try:
            self._check_cancellation() # Check at the start
            self.processing_status = "analyzing"
            self.progress = 10
            self.logger.info(f"Starting analysis of bundle: {self.bundle_path}")

            bundle_info = get_bundle_info(self.bundle_path, self.logger)
            self._check_cancellation() # Check during process
            self.progress = 20

            self.env = load_unity_environment(self.bundle_path, self.logger)
            self._check_cancellation() # Check during process
            self.progress = 40

            self.objects = list(self.env.objects)
            self.logger.info(f"Found {len(self.objects)} objects in bundle.")
            self._check_cancellation() # Check during process
            self.progress = 60
            
            asset_inventory = build_asset_inventory(self.objects, self.logger, self.app_config['DEBUG_MODE'])
            self._check_cancellation() # Check during process
            self.progress = 90
            
            asset_classes = sorted(list(asset_inventory.keys()))
            
            self.metadata = {
                'bundle_info': {
                    'filename': self.original_filename,
                    'size': bundle_info['size'],
                    'signature': bundle_info['signature'],
                    'compression': bundle_info['compression'],
                    'unity_version': str(getattr(self.env, 'unity_version', 'Unknown')),
                    'platform': str(getattr(self.env, 'platform', 'Unknown')),
                    'object_count': len(self.objects)
                },
                'assets': asset_inventory,
                'asset_classes': asset_classes,
                'analyzed_at': datetime.now().isoformat()
            }
            self.logger.info("Bundle analysis completed successfully.")
            self.processing_status = "completed"
            self.progress = 100

        except InterruptedError: # Catch explicit cancellation
            self.processing_status = "cancelled"
            self.error_message = "Task cancelled by user."
            self.logger.info(f"Analysis for session {self.session_id} stopped due to cancellation request.")
            self.cleanup() # Ensure cleanup on cancellation
        except Exception as e:
            self.processing_status = "error"
            self.error_message = f"Analysis failed: {traceback.format_exc() if self.app_config['DEBUG_MODE'] else str(e)}"
            self.logger.error(f"Analysis failed for {self.bundle_path}:", exc_info=True)
            self.cleanup()

    def extract_selected_assets(self, selected_indices: List[int]) -> str:
        """
        Orchestrates the extraction of assets specified by their indices.
        Each asset is exported to a temporary directory, and then all
        exported assets are packaged into a single ZIP archive.
        """
        try:
            self._check_cancellation() # Check at the start
            self.processing_status = "extracting"
            self.progress = 0
            self.logger.info(f"Starting extraction of {len(selected_indices)} assets for session {self.session_id}.")
            
            self.output_dir = tempfile.mkdtemp(prefix=f"extract_{self.session_id}_", dir=self.app_config['OUTPUT_FOLDER'])
            self.logger.debug(f"Temporary extraction directory created: {self.output_dir}")

            total_assets = len(selected_indices)
            for i, asset_index in enumerate(selected_indices):
                self._check_cancellation() # Check during loop
                if asset_index < 0 or asset_index >= len(self.objects):
                    self.logger.warning(f"Invalid asset index {asset_index} received. Skipping.")
                    continue

                obj = self.objects[asset_index]
                success = extract_single_asset_orchestrator(obj, self.output_dir, self.logger, self.app_config['DEBUG_MODE'])
                
                if success:
                    self.export_stats['success'] += 1
                else:
                    self.export_stats['failed'] += 1
                    self.logger.warning(f"Export function returned False for asset {get_object_name(obj)} ({obj.type.name}).")

                self.progress = int(((i + 1) / total_assets) * 90)
                
            self._check_cancellation() # Check before zipping
            self.progress = 95
            zip_path = create_archive(self.output_dir, self.original_filename, self.app_config['OUTPUT_FOLDER'], self.session_id, self.logger)
            self.progress = 100
            self.processing_status = "completed"
            
            self.logger.info(f"Extraction successful. Archive created at: {zip_path}")
            return zip_path
        except InterruptedError: # Catch explicit cancellation
            self.processing_status = "cancelled"
            self.error_message = "Task cancelled by user."
            self.logger.info(f"Extraction for session {self.session_id} stopped due to cancellation request.")
            self.cleanup()
            raise # Re-raise to ensure calling function also knows
        except Exception as e:
            self.processing_status = "error"
            self.error_message = f"Extraction failed: {traceback.format_exc() if self.app_config['DEBUG_MODE'] else str(e)}"
            self.logger.error(f"Extraction failed for session {self.session_id}: {e}", exc_info=True)
            self.cleanup()
            raise

    def cleanup(self):
        """
        Removes all temporary files and directories associated with this session.
        This includes uploaded files, extracted output, and session-specific logs.
        """
        self.logger.info(f"Initiating cleanup for session {self.session_id}.")
        try:
            if self.session_upload_dir and os.path.exists(self.session_upload_dir):
                shutil.rmtree(self.session_upload_dir, ignore_errors=True)
                self.logger.debug(f"Removed upload directory: {self.session_upload_dir}")
            
            if self.output_dir and os.path.exists(self.output_dir):
                shutil.rmtree(self.output_dir, ignore_errors=True)
                self.logger.debug(f"Removed output directory: {self.output_dir}")
            
            # Close and remove session logger handlers to release file locks
            for handler in self.logger.handlers[:]:
                handler.close()
                self.logger.removeHandler(handler)

            if os.path.exists(os.path.join(self.app_config['SESSION_LOGS_DIR'], self.session_id)):
                shutil.rmtree(os.path.join(self.app_config['SESSION_LOGS_DIR'], self.session_id), ignore_errors=True)
                self.logger.debug(f"Removed session log directory: {self.session_id}")

            self.logger.info(f"Cleanup completed for session {self.session_id}.")
        except Exception as e:
            logging.getLogger(__name__).warning(f"Cleanup warning for session {self.session_id}: {e}", exc_info=True)