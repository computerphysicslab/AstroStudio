"""Argv builders for optional external processing tools."""

from typing import List


class ExternalToolAdapter:
    """Build argv for optional backends that may not be installed."""

    def __init__(self, binary: str) -> None:
        self.binary = binary

    def develop_raw(self, source: str, output: str) -> List[str]:
        if "rawtherapee" in self.binary:
            return [self.binary, "-o", output, source]
        if "darktable" in self.binary:
            return [self.binary, source, output]
        return [self.binary, "-T", "-6", source]

    def panorama(self, inputs: List[str], output: str) -> List[str]:
        return [self.binary, "-o", output] + inputs

    def fuse(self, inputs: List[str], output: str) -> List[str]:
        return [self.binary, "-o", output] + inputs

    def gimp_script(self, script: str) -> List[str]:
        return [self.binary, "-i", "-b", script, "-b", "(gimp-quit 0)"]
