"""Core orchestration components."""

from .astrometry import find_output, find_plate_solution, summarize_solution
from .backends import BackendRegistry, BackendSpec, BackendStatus
from .command_builder import CommandBuilder
from .export_formats import EXPORT_FORMATS, ExportFormat, find_format
from .export_paths import unique_export_path
from .image_workspace import ImageWorkspace, Snapshot, WorkingImage
from .process_engine import JobResult, ProcessEngine
from .scratch import ScratchManager
from .settings import SettingsManager

__all__ = [
    "BackendRegistry",
    "BackendSpec",
    "BackendStatus",
    "CommandBuilder",
    "find_output",
    "find_plate_solution",
    "summarize_solution",
    "EXPORT_FORMATS",
    "ExportFormat",
    "find_format",
    "unique_export_path",
    "ImageWorkspace",
    "Snapshot",
    "WorkingImage",
    "JobResult",
    "ProcessEngine",
    "ScratchManager",
    "SettingsManager",
]
