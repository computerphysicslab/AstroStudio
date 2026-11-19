"""Discover standard astronomical calibration folders."""

import os
from typing import Dict, List

IMAGE_SUFFIXES = (
    ".fits", ".fit", ".fts", ".tif", ".tiff", ".png", ".jpg", ".jpeg",
    ".cr2", ".cr3", ".nef", ".arw", ".dng",
)

FOLDER_ALIASES = {
    "bias": ("bias", "biases"),
    "dark": ("dark", "darks"),
    "flat": ("flat", "flats"),
    "light": ("light", "lights"),
}


def _is_image(name: str) -> bool:
    return name.lower().endswith(IMAGE_SUFFIXES)


def discover_calibration(root: str) -> Dict[str, List[str]]:
    result: Dict[str, List[str]] = {key: [] for key in FOLDER_ALIASES}
    try:
        entries = sorted(os.listdir(root))
    except OSError:
        return result
    for name in entries:
        path = os.path.join(root, name)
        if os.path.isdir(path):
            for category, aliases in FOLDER_ALIASES.items():
                if name.lower() in aliases:
                    result[category].extend(
                        os.path.join(path, item)
                        for item in sorted(os.listdir(path))
                        if os.path.isfile(os.path.join(path, item)) and _is_image(item)
                    )
        elif _is_image(name):
            result["light"].append(path)
    return result
