"""CLI adapters for the initial phase of Astro Studio."""

from .base import CliAdapter
from .exiftool import ExifToolAdapter
from .magick import ImageMagickAdapter

__all__ = ["CliAdapter", "ExifToolAdapter", "ImageMagickAdapter"]
