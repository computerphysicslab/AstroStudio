"""Parse CLI histogram text into plottable (intensity, count) points."""

import re
from typing import List, Tuple

LINE_RE = re.compile(r"^\s*(\d+):\s*\(([^)]*)\)")


def histogram_argv(binary: str, path: str) -> list:
    """Bound the number of histogram lines before parsing them into the GUI."""
    return [
        binary,
        path,
        "-resize",
        "256x256!",
        "-colors",
        "256",
        "-format",
        "%c",
        "histogram:info:-",
    ]


def parse_histogram_text(text: str) -> List[Tuple[int, int]]:
    values: dict = {}
    for line in text.splitlines():
        match = LINE_RE.match(line)
        if not match:
            continue
        count = int(match.group(1))
        components = [
            int(float(component)) for component in match.group(2).split(",") if component.strip()
        ]
        if not components:
            continue
        intensity = max(0, min(255, int(sum(components) / len(components))))
        values[intensity] = values.get(intensity, 0) + count
    return sorted(values.items())
