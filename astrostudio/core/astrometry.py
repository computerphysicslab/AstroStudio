"""Helpers for reading astrometry artifacts written by external backends."""

import json
import os
import re
from typing import List, Optional, Tuple

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


def classify_backend_failure(detail: str) -> Tuple[str, str]:
    """Return a category and an actionable hint for a backend error message."""
    text = detail.lower()
    if "hips2fits" in text or ("404" in text and "hips" in text):
        return (
            "hips-service",
            "The CDS HiPS survey service is unavailable for the configured "
            "survey; change survey_hips in Options > Backend Settings or retry later.",
        )
    if "no consistent transform" in text or "0 matched pairs" in text:
        return (
            "solver-matching",
            "SkyStacker could not match stars in this field. Use a linear frame "
            "and a precise RA/Dec seed; a blind fallback needs astrometry.net or ASTAP.",
        )
    if "no catalog manifest" in text:
        return (
            "catalog-env",
            "SkyStacker could not find the blind catalog manifest; set "
            "SKYSTACKER_CATALOGS in Options > Backend Settings.",
        )
    if "no images found for operation" in text:
        return (
            "argv-order",
            "ImageMagick rejected the operation order; this is an AstroStudio bug.",
        )
    return "backend-error", "The external backend reported an error; no result was fabricated."


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
