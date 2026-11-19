"""Parse SkyStacker per-frame quality measurements."""

import json
from dataclasses import dataclass
from typing import List


@dataclass
class FrameDiagnostics:
    file: str
    width: int
    height: int
    stars: int
    hfr: float
    eccentricity: float
    bg_sigma: float
    snr: float
    quality: float


def parse_measurements(text: str) -> List[FrameDiagnostics]:
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        return []
    result = []
    for item in data.get("images", []):
        try:
            result.append(
                FrameDiagnostics(
                    file=item.get("file", ""),
                    width=int(item.get("width", 0)),
                    height=int(item.get("height", 0)),
                    stars=int(item.get("stars", 0)),
                    hfr=float(item.get("median_hfr_px", 0.0)),
                    eccentricity=float(item.get("median_eccentricity", 0.0)),
                    bg_sigma=float(item.get("bg_sigma", 0.0)),
                    snr=float(item.get("snr", 0.0)),
                    quality=float(item.get("quality", 0.0)),
                )
            )
        except (TypeError, ValueError):
            continue
    return result
