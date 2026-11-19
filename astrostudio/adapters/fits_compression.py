"""FITS compression adapters for external fpack/funpack and gzip."""

import shutil
from typing import List


class FitsCompressionAdapter:
    def __init__(self, binary: str) -> None:
        self.binary = binary

    def is_available(self) -> bool:
        return shutil.which(self.binary) is not None

    def pack_argv(self, source: str, destination: str, algorithm: str = "RICE_1") -> List[str]:
        if self.binary == "gzip":
            return ["gzip", "-kf", source]
        return [self.binary, "- %s" % algorithm, source, destination]

    def unpack_argv(self, source: str, destination: str) -> List[str]:
        if self.binary == "gzip":
            return ["gzip", "-dc", source]
        return [self.binary, "-", source, destination]


ALGORITHMS = ("RICE_1", "GZIP_1", "GZIP_2", "HCOMPRESS_1", "PLIO_1")
