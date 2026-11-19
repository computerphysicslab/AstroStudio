"""Core orchestration components."""

from .astrometry import find_output, find_plate_solution, summarize_solution
from .backends import BackendRegistry, BackendSpec, BackendStatus
from .command_builder import CommandBuilder
from .operation_log import OperationLog
from .estimator import Estimator, StageModel
from .export_formats import EXPORT_FORMATS, ExportFormat, find_format
from .export_paths import unique_export_path
from .histogram import parse_histogram_text
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
    "Estimator",
    "StageModel",
    "find_format",
    "parse_histogram_text",
    "unique_export_path",
    "ImageWorkspace",
    "OperationLog",
    "Snapshot",
    "WorkingImage",
    "JobResult",
    "ProcessEngine",
    "ScratchManager",
    "SettingsManager",
]
