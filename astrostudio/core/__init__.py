"""Core orchestration components."""

from .astrometry import find_output, summarize_solution
from .backends import BackendRegistry, BackendSpec, BackendStatus
from .command_builder import CommandBuilder
from .export_formats import EXPORT_FORMATS, ExportFormat, find_format
from .image_workspace import ImageWorkspace, Snapshot, WorkingImage
from .process_engine import JobResult, ProcessEngine
from .scratch import ScratchManager

__all__ = [
    "BackendRegistry",
    "BackendSpec",
    "BackendStatus",
    "CommandBuilder",
    "find_output",
    "summarize_solution",
    "EXPORT_FORMATS",
    "ExportFormat",
    "find_format",
    "ImageWorkspace",
    "Snapshot",
    "WorkingImage",
    "JobResult",
    "ProcessEngine",
    "ScratchManager",
]
