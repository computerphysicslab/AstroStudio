"""Non-destructive metadata enrichment from successful plate solutions.

Original captures are read-only. Proposed astrometric tags are merged into a
JSON sidecar: existing keys are never removed or overwritten, coherent values
are kept, and conflicting values are reported instead of replaced.
"""

import json
import os
from typing import Any, Dict, List, Tuple

from .plate_solution import PlateSolution

SIDECAR_SUFFIX = ".metadata.json"
RA_DEC_TOLERANCE_DEG = 0.01


def proposed_tags(solution: PlateSolution) -> Dict[str, Any]:
    """Return the astrometric tags that can be proposed for an image."""
    return {
        "RA_DEG": round(solution.ra_deg, 6),
        "DEC_DEG": round(solution.dec_deg, 6),
        "PIXEL_SCALE_ARCSEC": round(solution.scale_arcsec_per_px, 3),
        "FOV_WIDTH_DEG": round(solution.fov_width_deg, 5),
        "FOV_HEIGHT_DEG": round(solution.fov_height_deg, 5),
        "PLATE_SOLUTION_METHOD": solution.method,
    }


def _coherent(existing: Any, proposed: Any, key: str) -> bool:
    if isinstance(existing, (int, float)) and isinstance(proposed, (int, float)):
        if key in ("RA_DEG", "DEC_DEG"):
            return abs(float(existing) - float(proposed)) <= RA_DEC_TOLERANCE_DEG
        tolerance = max(abs(float(proposed)) * 0.01, 1e-6)
        return abs(float(existing) - float(proposed)) <= tolerance
    return str(existing).strip().lower() == str(proposed).strip().lower()


def merge_metadata(
    existing: Dict[str, Any], proposed: Dict[str, Any]
) -> Tuple[Dict[str, Any], List[str], List[str]]:
    """Merge proposed tags without deleting or overwriting existing metadata."""
    merged: Dict[str, Any] = dict(existing)
    added: List[str] = []
    conflicts: List[str] = []
    for key, value in proposed.items():
        if key not in merged or merged[key] in (None, ""):
            merged[key] = value
            added.append(key)
        elif not _coherent(merged[key], value, key):
            conflicts.append(key)
    return merged, added, conflicts


def load_sidecar(directory: str, base: str) -> Dict[str, Any]:
    """Read the metadata dictionary from a previous sidecar, if any."""
    path = os.path.join(directory, base + SIDECAR_SUFFIX)
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        return {}
    metadata = data.get("metadata") if isinstance(data, dict) else None
    return metadata if isinstance(metadata, dict) else {}


def write_metadata_sidecar(
    directory: str,
    base: str,
    metadata: Dict[str, Any],
    added: List[str],
    conflicts: List[str],
    solution_path: str,
) -> str:
    """Write the merged metadata and its provenance to a JSON sidecar."""
    os.makedirs(directory, exist_ok=True)
    path = os.path.join(directory, base + SIDECAR_SUFFIX)
    payload = {
        "metadata": metadata,
        "added": added,
        "conflicts": conflicts,
        "source": os.path.basename(solution_path),
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return path
