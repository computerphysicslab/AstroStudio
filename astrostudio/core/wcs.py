"""Translate SkyStacker plate solutions into FITS WCS header values.

SkyStacker stores CRVAL in radians, CD in radians/pixel and CRPIX 0-based
(docs/plate-solving.md section 5). Installed tools cannot edit FITS headers
directly, so a JSON sidecar is written next to exported FITS files.
"""

import json
import math
import os
from typing import Any, Dict, Tuple


def wcs_cards(solution: Dict[str, Any]) -> Dict[str, Any]:
    wcs = solution["WCS"]
    cd = wcs["CD"]
    return {
        "CTYPE1": "RA---TAN",
        "CTYPE2": "DEC--TAN",
        "CRVAL1": math.degrees(float(wcs["CRVAL1"])),
        "CRVAL2": math.degrees(float(wcs["CRVAL2"])),
        "CRPIX1": float(wcs["CRPIX1"]) + 1.0,
        "CRPIX2": float(wcs["CRPIX2"]) + 1.0,
        "CD1_1": float(cd[0][0]) * 180.0 / math.pi,
        "CD1_2": float(cd[0][1]) * 180.0 / math.pi,
        "CD2_1": float(cd[1][0]) * 180.0 / math.pi,
        "CD2_2": float(cd[1][1]) * 180.0 / math.pi,
        "METHOD": solution.get("Method", "unknown"),
    }


def overlay_center(solution: Dict[str, Any]) -> Tuple[float, float]:
    """Return canvas pixel coordinates from the plate solution's 0-based CRPIX."""
    wcs = solution["WCS"]
    return float(wcs["CRPIX1"]), float(wcs["CRPIX2"])


def write_wcs_sidecar(fits_path: str, solution: Dict[str, Any]) -> str:
    path = os.path.splitext(fits_path)[0] + ".wcs.json"
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(wcs_cards(solution), handle, indent=2, sort_keys=True)
        handle.write("\n")
    return path
