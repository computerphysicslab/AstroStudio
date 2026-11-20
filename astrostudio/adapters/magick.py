"""ImageMagick connector: TIFF workspace and display-oriented operations."""

import shutil
from typing import TYPE_CHECKING, List, Sequence

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
        self.thread_limit = 0
        self.batch_binary = "mogrify"
        super().__init__(
            CommandBuilder(
                self.binary,
                flag_specs=(
                    ("-crop", "crop", None),
                    ("-resize", "resize", None),
                    ("-rotate", "rotate", lambda value: [str(value), "+repage"]),
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

    def _with_threads(self, argv: Sequence[str]) -> List[str]:
        result = list(argv)
        if self.thread_limit > 0:
            result[1:1] = ["-limit", "thread", str(int(self.thread_limit))]
        return result

    def build_argv(self, inputs, output=None, params=None):
        return self._with_threads(super().build_argv(inputs, output, params))

    def build_import_argv(self, source: str, tiff_path: str) -> Sequence[str]:
        """Import a source file into the high-depth working TIFF."""
        lowered = source.lower()
        if lowered.endswith((".fits", ".fit", ".fts")):
            # ImageMagick writes RGB FITS as three grayscale HDUs; -combine
            # restores them to one RGB working TIFF.
            return self._with_threads([self.binary, source, "-combine", "-depth", "16", tiff_path])
        if lowered.endswith((".psd", ".psb")):
            # Flatten all layers into one composite frame before writing the TIFF.
            return [self.binary, source, "-flatten", "-depth", "16", tiff_path]
        return self._with_threads([self.binary, source, "-depth", "16", tiff_path])

    def build_preview_argv(
        self,
        tiff_path: str,
        png_path: str,
        display_stretch: bool = False,
        stretch_points: tuple = None,
        gamma: float = None,
    ) -> Sequence[str]:
        argv = [self.binary, tiff_path]
        if gamma is not None:
            argv.extend(("-evaluate", "Pow", "%.3f" % float(gamma)))
        elif display_stretch:
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
        return self._with_threads(argv)

    def build_diff_argv(self, current_tiff: str, before_tiff: str, output_png: str) -> List[str]:
        """Create a stretched difference map between two TIFF snapshots."""
        return self._with_threads(
            [
                self.binary,
                current_tiff,
                before_tiff,
                "-compose",
                "difference",
                "-composite",
                "-auto-level",
                "-depth",
                "8",
                output_png,
            ]
        )

    def build_batch_argv(
        self, inputs: Sequence[str], output_dir: str, extension: str
    ) -> List[str]:
        argv = [
            self.batch_binary,
            "-format",
            extension.lstrip("."),
            "-path",
            output_dir,
        ]
        argv.extend(inputs)
        return self._with_threads(argv)

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
        return self._with_threads(argv)

    def build_display_export_argv(
        self,
        tiff_path: str,
        destination: str,
        export_format: "ExportFormat",
        gamma: float = None,
        stretch_points: tuple = None,
    ) -> Sequence[str]:
        argv = [self.binary, tiff_path]
        if gamma is not None:
            argv.extend(("-evaluate", "Pow", "%.3f" % float(gamma)))
        if stretch_points:
            low, high = stretch_points
            argv.extend(
                (
                    "-level",
                    "%.1f%%,%.1f%%" % (low / 255.0 * 100.0, high / 255.0 * 100.0),
                )
            )
        argv.extend(export_format.flags)
        argv.append(destination)
        return self._with_threads(argv)
