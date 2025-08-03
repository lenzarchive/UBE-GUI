# -*- coding: utf-8 -*-
"""
UnityBundleExtractor - Mesh Exporter Module
Author: lenzarchive (https://github.com/lenzarchive)
License: MIT License

This module provides a standalone function for exporting Unity Mesh assets to OBJ format.
"""

import os
import json
import logging
from typing import Any, Optional

# Configure logger for this module
logger = logging.getLogger(__name__)

def _calculate_bounds(vertices) -> Optional[dict]:
    """
    Calculates the axis-aligned bounding box (AABB) for a given set of vertices.
    """
    if not vertices:
        return None
    min_coords = [float('inf')] * 3
    max_coords = [float('-inf')] * 3
    for vertex in vertices:
        if len(vertex) >= 3:
            for i in range(3):
                min_coords[i] = min(min_coords[i], vertex[i])
                max_coords[i] = max(max_coords[i], vertex[i])
    
    return {
        'min': min_coords,
        'max': max_coords,
        'center': [(min_coords[i] + max_coords[i]) / 2 for i in range(3)],
        'size': [max_coords[i] - min_coords[i] for i in range(3)]
    }

def export_mesh_obj(data: Any, output_path: str, debug_mode: bool, local_logger: logging.Logger) -> bool:
    """
    Exports a Mesh asset to a Wavefront .obj file. Includes vertex, normal,
    and UV data if available. Also generates a metadata JSON file.

    Args:
        data (Any): The UnityPy object data for the mesh.
        output_path (str): The base path for the output file (without extension).
        debug_mode (bool): Flag indicating if the application is in debug mode.
        local_logger (logging.Logger): The logger instance for recording messages.

    Returns:
        bool: True if the mesh was successfully exported, False otherwise.
    """
    try:
        local_logger.debug(f"Attempting to export Mesh: {output_path}")
        vertices = getattr(data, 'm_Vertices', [])
        indices = getattr(data, 'm_IndexBuffer', [])
        normals = getattr(data, 'm_Normals', [])
        uvs = getattr(data, 'm_UV', [])
        
        if not vertices:
            local_logger.debug(f"Mesh {output_path} has no vertices, skipping export.")
            return False
        
        obj_lines = [
            f"# Wavefront OBJ file exported by UnityBundleExtractor",
            f"# Source Mesh: {getattr(data, 'm_Name', 'Unknown')}",
            f"# Vertices: {len(vertices)}",
            f"# Faces: {len(indices) // 3 if indices else 0}",
            ""
        ]
        
        # Write vertices
        for v in vertices:
            if len(v) >= 3:
                obj_lines.append(f"v {v[0]} {v[1]} {v[2]}")
        
        # Write normals
        if normals:
            obj_lines.append("")
            for n in normals:
                if len(n) >= 3:
                    obj_lines.append(f"vn {n[0]} {n[1]} {n[2]}")
        
        # Write UVs (texture coordinates)
        if uvs:
            obj_lines.append("")
            for uv in uvs:
                if len(uv) >= 2:
                    obj_lines.append(f"vt {uv[0]} {uv[1]}")

        # Write faces
        if indices:
            obj_lines.append("\ng mesh")
            for i in range(0, len(indices) - 2, 3):
                # OBJ indices are 1-based
                v1, v2, v3 = indices[i] + 1, indices[i+1] + 1, indices[i+2] + 1
                face_str = "f"
                if normals and uvs:
                    face_str += f" {v1}/{v1}/{v1} {v2}/{v2}/{v2} {v3}/{v3}/{v3}"
                elif uvs:
                    face_str += f" {v1}/{v1} {v2}/{v2} {v3}/{v3}"
                elif normals:
                    face_str += f" {v1}//{v1} {v2}//{v2} {v3}//{v3}"
                else:
                    face_str += f" {v1} {v2} {v3}"
                obj_lines.append(face_str)

        with open(f"{output_path}.obj", 'w', encoding='utf-8') as f:
            f.write('\n'.join(obj_lines))
        
        # Save mesh metadata
        metadata = {
            'vertex_count': len(vertices),
            'triangle_count': len(indices) // 3 if indices else 0,
            'has_normals': bool(normals),
            'has_uvs': bool(uvs),
            'bounds': _calculate_bounds(vertices)
        }
        with open(f"{output_path}_meta.json", 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2)

        local_logger.debug(f"Mesh {output_path} saved as OBJ.")
        return True
    except Exception as e:
        local_logger.error(f"OBJ export failed for {output_path}: {e}", exc_info=debug_mode)
        return False