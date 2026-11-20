"""Parse SkyStacker star catalogs and build a portable SVG identification layer."""

import csv
import json
from dataclasses import dataclass
from typing import List


@dataclass
class StarDetection:
    x: float
    y: float
    flux: float
    size: float
    eccentricity: float
    hfr: float


def parse_star_catalog(text: str, extension: str = ".json") -> List[StarDetection]:
    detections: List[StarDetection] = []
    if extension.lower() == ".csv":
        reader = csv.DictReader(text.splitlines())
        for row in reader:
            try:
                detections.append(
                    StarDetection(
                        float(row["x_px"]),
                        float(row["y_px"]),
                        float(row["flux"]),
                        float(row["size_px"]),
                        float(row["eccentricity"]),
                        float(row["hfr_px"]),
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
        return detections

    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        return detections
    for item in data.get("stars", []):
        try:
            detections.append(
                StarDetection(
                    float(item["x_px"]),
                    float(item["y_px"]),
                    float(item["flux"]),
                    float(item.get("size_px", 0.0)),
                    float(item.get("eccentricity", 0.0)),
                    float(item.get("hfr_px", 0.0)),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    return detections


def write_star_layer_svg(
    path: str, detections: List[StarDetection], width: int, height: int
) -> str:
    top_flux = max((item.flux for item in detections), default=1.0) or 1.0
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (width, height, width, height),
        '<g id="star-identification" class="astro-studio-layer">',
    ]
    for rank, star in enumerate(detections, start=1):
        intensity = star.flux / top_flux
        radius = max(3.0, 11.0 - intensity * 7.0)
        lines.append(
            '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="#ffcc4d" '
            'stroke-width="1.2" opacity="%.2f"/>'
            % (star.x, star.y, radius, 0.4 + intensity * 0.6)
        )
        lines.append(
            '<text x="%.1f" y="%.1f" fill="#ffcc4d" font-size="9">%d</text>'
            % (star.x + radius + 2, star.y - radius - 1, rank)
        )
    lines.append("</g>")
    lines.append("</svg>")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    return path
