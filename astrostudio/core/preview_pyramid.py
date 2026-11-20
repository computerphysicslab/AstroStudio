"""Resolution-pyramid descriptors for large preview images."""

import os
from typing import List, Optional, Tuple

Level = Tuple[str, float]

PYRAMID_LEVELS = (
    ("preview_25.png", 0.25),
    ("preview_50.png", 0.5),
)


def pyramid_paths(directory: str) -> List[Level]:
    levels = []
    for name, scale in PYRAMID_LEVELS:
        path = os.path.join(directory, name)
        if os.path.isfile(path):
            levels.append((path, scale))
    return levels


def choose_level(levels: List[Level], display_scale: float) -> Optional[Level]:
    """Pick the finest level that is not much larger than the viewport scale."""
    if not levels:
        return None
    candidates = [level for level in levels if level[1] <= max(display_scale * 2.0, 0.25)]
    if not candidates:
        return min(levels, key=lambda level: level[1])
    return max(candidates, key=lambda level: level[1])
