"""ExifTool connector: read-only metadata extraction for the inspector."""

from typing import Any, Dict, List, Optional, Sequence

from ..core.command_builder import CommandBuilder
from .base import CliAdapter


class ExifToolAdapter(CliAdapter):
    name = "ExifTool"
    binary = "exiftool"
    description = "Read-only EXIF and FITS metadata tables"
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
    fields = ("filename", "exptime", "iso", "fnumber", "datetimeoriginal")

    def __init__(self) -> None:
        super().__init__(
            CommandBuilder(self.binary, flag_specs=(("-T", "tabular", None),), defaults={"tabular": True})
        )

    def build_argv(
        self,
        inputs: Sequence[str],
        output: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        argv = self.builder.build(inputs, output, params)
        field_flags = ["-" + field for field in self.fields]
        return argv[:1] + field_flags + argv[1:]
