"""Non-destructive markup annotations burned in by an external CLI at export."""

from dataclasses import dataclass
from typing import Any, List


@dataclass
class Annotation:
    kind: str
    x: float
    y: float
    text: str = ""
    x2: float = 0.0
    y2: float = 0.0
    colour: str = "red"


def draw_command(annotation: Annotation) -> str:
    if annotation.kind == "arrow":
        return "stroke %s fill none line %d,%d %d,%d" % (
            annotation.colour, annotation.x, annotation.y, annotation.x2, annotation.y2
        )
    if annotation.kind == "circle":
        return "stroke %s fill none circle %d,%d %d,%d" % (
            annotation.colour, annotation.x, annotation.y, annotation.x2, annotation.y2
        )
    return "fill %s text %d,%d '%s'" % (
        annotation.colour, annotation.x, annotation.y, annotation.text
    )


def build_annotate_argv(
    adapter: Any,
    tiff_path: str,
    annotations: List[Annotation],
    output_png: str,
) -> List[str]:
    argv = [adapter.binary, tiff_path]
    for item in annotations:
        argv.extend(("-draw", draw_command(item)))
    argv.extend(("-depth", "8", output_png))
    return list(adapter._with_threads(argv))
