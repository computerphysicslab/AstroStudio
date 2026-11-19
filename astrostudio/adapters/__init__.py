"""CLI adapters for the initial phase of Astro Studio."""

from .base import CliAdapter
from .exiftool import ExifToolAdapter
from .magick import ImageMagickAdapter
from .siril import SirilAdapter
from .skystacker import SkyStackerAdapter

__all__ = [
    "CliAdapter",
    "ExifToolAdapter",
    "ImageMagickAdapter",
    "SirilAdapter",
    "SkyStackerAdapter",
]
