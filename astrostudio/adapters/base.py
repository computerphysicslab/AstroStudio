"""Base class for external CLI tool connectors."""

import os
import shutil
from typing import Any, Dict, List, Optional, Sequence

from ..core.command_builder import CommandBuilder


class CliAdapter:
    """Base contract for a CLI connector.

    Subclasses declare supported formats and implement ``build_*_argv`` methods that
    return argv lists. Methods must never concatenate shell strings, must never modify
    original inputs, and must always write products to a caller-provided scratch path.
    """

    name = ""
    binary = ""
    description = ""
    input_formats: Sequence[str] = ()
    output_formats: Sequence[str] = ()

    def __init__(self, builder: CommandBuilder) -> None:
        self.builder = builder

    def is_available(self) -> bool:
        """Return whether the configured binary can be found on PATH."""
        return shutil.which(self.binary) is not None

    def build_argv(
        self,
        inputs: Sequence[str],
        output: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        """Serialize a transform into an argv list; override only when needed."""
        return self.builder.build(inputs, output, params)

    @staticmethod
    def output_path(job_dir: str, source: str, extension: str) -> str:
        stem = os.path.splitext(os.path.basename(source))[0]
        safe_stem = "".join(
            character if character.isalnum() or character in "-_" else "_"
            for character in stem
        )
        suffix = extension.lstrip(".")
        return os.path.join(job_dir, "%s_processed.%s" % (safe_stem, suffix))

    def supports_input(self, path: str) -> bool:
        extension = os.path.splitext(path)[1].lstrip(".").lower()
        return extension in self.input_formats
