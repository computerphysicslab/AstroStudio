"""CLI adapters for the initial phase of Astro Studio."""

from .astrometry import AstrometryAdapter
from .base import CliAdapter
from .external_pipelines import ExternalToolAdapter
from .exiftool import ExifToolAdapter
from .magick import ImageMagickAdapter
from .siril import SirilAdapter
from .skystacker import SkyStackerAdapter

__all__ = [
    "AstrometryAdapter",
    "CliAdapter",
    "ExternalToolAdapter",
    "ExifToolAdapter",
    "ImageMagickAdapter",
    "SirilAdapter",
    "SkyStackerAdapter",
]
