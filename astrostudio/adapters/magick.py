"""ImageMagick connector: format conversion and display-oriented operations."""

from ..core.command_builder import CommandBuilder
from .base import CliAdapter


class ImageMagickAdapter(CliAdapter):
    name = "ImageMagick"
    binary = "magick"
    description = "Raster format conversion, resize and display sharpening"
    input_formats = ("jpg", "jpeg", "png", "tif", "tiff", "bmp", "webp")
    output_formats = ("png", "jpg", "jpeg", "tif", "tiff", "bmp")

    def __init__(self) -> None:
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
