"""ImageMagick connector: TIFF workspace and display-oriented operations."""

import shutil
from typing import TYPE_CHECKING, Sequence

if TYPE_CHECKING:
    from ..core.export_formats import ExportFormat

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
                    ("-blur", "blur", None),
                    ("-gaussian-blur", "gaussian-blur", None),
                    ("-median", "median", None),
                    ("-despeckle", "despeckle", None),
                    ("-adaptive-blur", "adaptive-blur", None),
                    ("-sharpen", "sharpen", None),
                    ("-convolve", "convolve", None),
                    ("-morphology", "morphology", lambda value: str(value).split()),
                    ("-edge", "edge", None),
                    ("-emboss", "emboss", None),
                ),
            )
        )

    def build_import_argv(self, source: str, tiff_path: str) -> Sequence[str]:
        if source.lower().endswith((".fits", ".fit", ".fts")):
            # ImageMagick writes RGB FITS as three grayscale HDUs; -combine
            # restores them to one RGB working TIFF.
            return [self.binary, source, "-combine", "-depth", "16", tiff_path]
        return [self.binary, source, "-depth", "16", tiff_path]

    def build_preview_argv(
        self,
        tiff_path: str,
        png_path: str,
        display_stretch: bool = False,
        stretch_points: tuple = None,
    ) -> Sequence[str]:
        argv = [self.binary, tiff_path]
        if display_stretch:
            argv.extend(("-evaluate", "Pow", "0.45"))
        if stretch_points:
            low, high = stretch_points
            argv.extend(
                (
                    "-level",
                    "%.1f%%,%.1f%%" % (low / 255.0 * 100.0, high / 255.0 * 100.0),
                )
            )
        argv.extend(("-depth", "8", png_path))
        return argv

    def build_export_argv(
        self,
        tiff_path: str,
        destination: str,
        export_format: "ExportFormat" = None,
    ) -> Sequence[str]:
        argv = [self.binary, tiff_path]
        if export_format:
            argv.extend(export_format.flags)
        argv.append(destination)
        return argv
