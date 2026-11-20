"""Parse SkyStacker diffuse-object reports and build identification layers."""

import json
from dataclasses import dataclass
from typing import List


@dataclass
class DiffuseObject:
    id: int
    x: float
    y: float
    area: int
    flux: float
    concentration: float
    asymmetry: float
    smoothness: float
    gini: float
    m20: float
    ellipticity: float
    object_type: str


def parse_classification(text: str):
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        return [], {}
    objects = []
    for item in data.get("objects", []):
        try:
            objects.append(
                DiffuseObject(
                    int(item.get("id", 0)),
                    float(item["x_px"]),
                    float(item["y_px"]),
                    int(item.get("area_px", 0)),
                    float(item.get("flux", 0.0)),
                    float(item.get("concentration", 0.0)),
                    float(item.get("asymmetry", 0.0)),
                    float(item.get("smoothness", 0.0)),
                    float(item.get("gini", 0.0)),
                    float(item.get("m20", 0.0)),
                    float(item.get("ellipticity", 0.0)),
                    str(item.get("object_type", "unknown")),
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    report = {
        "image": data.get("image", ""),
        "width": data.get("width", 0),
        "height": data.get("height", 0),
        "threshold_sigma": data.get("threshold_sigma", 3.0),
        "star_mask_pixels": data.get("star_mask_pixels", 0),
        "count": data.get("count", len(objects)),
        "standards": data.get("standards", {}),
    }
    return objects, report


def write_object_layer_svg(
    path: str, objects: List[DiffuseObject], width: int, height: int
) -> str:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d">' % (width, height, width, height),
        '<g id="diffuse-objects" class="astro-studio-layer">',
    ]
    for obj in objects:
        radius = max(6.0, min(60.0, obj.area ** 0.5 / 2.0))
        lines.append(
            '<circle cx="%.1f" cy="%.1f" r="%.1f" fill="none" stroke="#8ed1fc" '
            'stroke-width="1.4" opacity="0.85"/>'
            % (obj.x, obj.y, radius)
        )
        lines.append(
            '<text x="%.1f" y="%.1f" fill="#8ed1fc" font-size="10">%d: %s</text>'
            % (obj.x + radius + 2, obj.y - radius - 2, obj.id, obj.object_type)
        )
    lines.append("</g>")
    lines.append("</svg>")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    return path
