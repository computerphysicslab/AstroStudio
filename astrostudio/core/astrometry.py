"""Helpers for reading astrometry artifacts written by external backends."""

import json
import os
import re
from typing import List, Optional

PREFERRED_KEYS = ("fov", "field", "ra", "dec", "scale", "center", "width", "height")


def find_plate_solution(directory: str) -> Optional[str]:
    """Locate a plate solution JSON (canonical name preferred)."""
    for root, _dirs, files in os.walk(directory):
        if "plate_solution.json" in files:
            return os.path.join(root, "plate_solution.json")
    return find_output(directory, ["_plate_solution.json"])


def find_output(directory: str, suffixes: List[str]) -> Optional[str]:
    for root, _dirs, files in os.walk(directory):
        for name in sorted(files):
            if name.lower().endswith(tuple(suffixes)):
                return os.path.join(root, name)
    return None


def strip_svg_titles(svg_path: str, output_path: str) -> str:
    """Copy an SVG without <title> nodes, which ImageMagick 7 silently skips.

    SkyStacker uses <title> children for star tooltips. Its MSVG renderer
    drops the whole enclosing <circle> when a title is present, leaving an
    apparently empty map. The visual geometry is unchanged.
    """
    with open(svg_path, "r", encoding="utf-8") as handle:
        content = handle.read()
    cleaned = re.sub(r"<title>.*?</title>", "", content, flags=re.DOTALL)
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(cleaned)
    return output_path


def sky_map_source_count(svg_path: str) -> int:
    """Count plotted point-source markers in a SkyStacker sky-map SVG."""
    try:
        with open(svg_path, "r", encoding="utf-8") as handle:
            return handle.read().count("<circle")
    except OSError:
        return 0


def summarize_solution(path: str) -> str:
    """Return a readable summary of a plate-solution JSON report."""
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError) as exc:
        return "Cannot read plate solution %s: %s" % (path, exc)

    scalar = {
        key: value
        for key, value in data.items()
        if isinstance(value, (str, int, float, bool))
    }
    if not scalar:
        return "Plate solution %s contains no scalar values" % path

    ordered = []
    for keyword in PREFERRED_KEYS:
        for key, value in scalar.items():
            if keyword in key.lower() and key not in ordered:
                ordered.append(key)
    for key in scalar:
        if key not in ordered:
            ordered.append(key)
    return "\n".join("%s: %s" % (key, scalar[key]) for key in ordered[:16])
