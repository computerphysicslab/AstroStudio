"""Export format catalog used by the Save As / Export dialog."""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ExportFormat:
    key: str
    label: str
    extension: str
    category: str
    flags: Tuple[str, ...] = ()
    description: str = ""


EXPORT_FORMATS: Tuple[ExportFormat, ...] = (
    ExportFormat(
        "tiff16",
        "TIFF 16-bit - linear, uncompressed",
        "tif",
        "Scientific",
        ("-depth", "16", "-compress", "None"),
        "Maximum colour depth, no compression",
    ),
    ExportFormat(
        "tiff16-lzw",
        "TIFF 16-bit - LZW compressed",
        "tif",
        "Scientific",
        ("-depth", "16", "-compress", "LZW"),
        "Lossless compression, linear data",
    ),
    ExportFormat(
        "tiff16-zip",
        "TIFF 16-bit - Zip compressed",
        "tif",
        "Scientific",
        ("-depth", "16", "-compress", "Zip"),
        "Lossless compression, linear data",
    ),
    ExportFormat(
        "fits16",
        "FITS - astronomical 16-bit",
        "fits",
        "Scientific",
        ("-depth", "16"),
        "FITS header support via the external backend",
    ),
    ExportFormat(
        "png8",
        "PNG 8-bit - display preview",
        "png",
        "Display",
        ("-depth", "8"),
        "Lossless, no compression artefacts",
    ),
    ExportFormat(
        "jpg90",
        "JPEG 8-bit - 90% quality",
        "jpg",
        "Display",
        ("-depth", "8", "-quality", "90"),
        "Lossy compression, small files",
    ),
    ExportFormat(
        "jpg95",
        "JPEG 8-bit - 95% quality",
        "jpg",
        "Display",
        ("-depth", "8", "-quality", "95"),
        "Lossy compression, higher quality",
    ),
    ExportFormat(
        "bmp8",
        "BMP 8-bit - uncompressed",
        "bmp",
        "Display",
        ("-depth", "8"),
        "Uncompressed display format",
    ),
)


def find_format(key: str) -> ExportFormat:
    for export_format in EXPORT_FORMATS:
        if export_format.key == key:
            return export_format
    return EXPORT_FORMATS[0]
