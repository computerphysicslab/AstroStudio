"""ExifTool connector: read-only metadata extraction for the inspector."""

from typing import Any, Dict, List, Optional, Sequence

from ..core.command_builder import CommandBuilder
from .base import CliAdapter


class ExifToolAdapter(CliAdapter):
    name = "ExifTool"
    binary = "exiftool"
    description = "Read-only EXIF and FITS metadata for the inspector"
    input_formats = (
        "jpg",
        "jpeg",
        "png",
        "tif",
        "tiff",
        "bmp",
        "cr2",
        "nef",
        "arw",
        "dng",
        "fits",
        "fit",
        "xisf",
    )
    fields = (
        "FileType",
        "Make",
        "Model",
        "LensID",
        "ExposureTime",
        "ISO",
        "FNumber",
        "FocalLength",
        "DateTimeOriginal",
        "ImageWidth",
        "ImageHeight",
        "BitsPerSample",
    )

    def __init__(self) -> None:
        super().__init__(CommandBuilder(self.binary))

    def build_argv(
        self,
        inputs: Sequence[str],
        output: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        return (
            [self.binary, "-s"]
            + ["-" + field for field in self.fields]
            + list(inputs)
        )
