"""ImageMagick connector: TIFF workspace and display-oriented operations."""

import shutil
from typing import Optional, Sequence

from ..core.command_builder import CommandBuilder
from .base import CliAdapter


class ImageMagickAdapter(CliAdapter):
    name = "ImageMagick"
    description = "High-depth TIFF workspace, CLI transforms and PNG previews"
    input_formats = ("jpg", "jpeg", "png", "tif", "tiff", "bmp", "webp", "fits", "fit")
    output_formats = ("png", "jpg", "jpeg", "tif", "tiff", "bmp")

    def __init__(self, binary: str = None) -> None:
        self.binary = binary or (
            "magick" if shutil.which("magick") else "convert"
        )
        super().__init__(
            CommandBuilder(
                self.binary,
                flag_specs=(
                    ("-crop", "crop", None),
                    ("-resize", "resize", None),
                    ("-rotate", "rotate", None),
                    ("-unsharp", "unsharp", None),
                ),
            )
        )

    def build_import_argv(self, source: str, tiff_path: str) -> Sequence[str]:
        return [self.binary, source, "-depth", "16", tiff_path]

    def build_preview_argv(self, tiff_path: str, png_path: str) -> Sequence[str]:
        return [self.binary, tiff_path, "-depth", "8", png_path]

    def build_export_argv(self, tiff_path: str, destination: str) -> Sequence[str]:
        return self.build_argv([tiff_path], destination)
