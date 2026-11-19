"""Translate SkyStacker plate_solution.json into UI-friendly quantities.

Angles in JSON are radians and CD is radians/pixel (docs/plate-solving.md §5).
"""

import json
import math
import os
from dataclasses import dataclass
from typing import Dict, Optional

RADEG = 180.0 / math.pi
ARCSEC = 206264.806


@dataclass
class PlateSolution:
    ra_deg: float
    dec_deg: float
    scale_arcsec_per_px: float
    fov_width_deg: float
    fov_height_deg: float
    orientation_deg: float
    method: str
    rms_arcsec: float
    matches: int
    stars: int
    path: str

    def summary(self) -> str:
        return (
            "Method: %s\n"
            "Center: RA %.5f deg, Dec %.5f deg\n"
            "Pixel scale: %.3f arcsec/px\n"
            "Field of view: %.4f x %.4f deg\n"
            "Orientation: %.2f deg\n"
            "RMS: %.3f arcsec (%d/%d matches)"
            % (
                self.method,
                self.ra_deg,
                self.dec_deg,
                self.scale_arcsec_per_px,
                self.fov_width_deg,
                self.fov_height_deg,
                self.orientation_deg,
                self.rms_arcsec,
                self.matches,
                self.stars,
            )
        )


def load_solution(path: str, width: int, height: int) -> PlateSolution:
    with open(path, "r", encoding="utf-8") as handle:
        data: Dict = json.load(handle)
    wcs = data["WCS"]
    cd = wcs["CD"]
    determinant = cd[0][0] * cd[1][1] - cd[0][1] * cd[1][0]
    scale = math.sqrt(abs(determinant)) * ARCSEC
    return PlateSolution(
        ra_deg=float(wcs["CRVAL1"]) * RADEG,
        dec_deg=float(wcs["CRVAL2"]) * RADEG,
        scale_arcsec_per_px=scale,
        fov_width_deg=width * scale / 3600.0,
        fov_height_deg=height * scale / 3600.0,
        orientation_deg=math.degrees(math.atan2(cd[0][1], cd[1][1])),
        method=data.get("Method", "unknown"),
        rms_arcsec=float(data.get("RMSArcsec", 0.0)),
        matches=int(data.get("NMatches", 0)),
        stars=int(data.get("NStars", 0)),
        path=path,
    )


def solution_for_directory(directory: str, width: int, height: int) -> Optional[PlateSolution]:
    from .astrometry import find_plate_solution

    path = find_plate_solution(directory)
    if not path or not os.path.isfile(path):
        return None
    try:
        return load_solution(path, width, height)
    except (OSError, ValueError, KeyError, TypeError):
        return None
