"""Core orchestration components."""

from .astrometry import find_output, find_plate_solution, summarize_solution
from .backends import BackendRegistry, BackendSpec, BackendStatus
from .command_builder import CommandBuilder
from .operation_log import OperationLog
from .package_info import install_command, package_for_binary, parse_policy
from .plate_solution import PlateSolution, load_solution, solution_for_directory
from .estimator import Estimator, StageModel
from .export_formats import EXPORT_FORMATS, ExportFormat, find_format
from .export_paths import unique_export_path
from .histogram import histogram_argv, parse_histogram_text
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
    "histogram_argv",
    "parse_histogram_text",
    "unique_export_path",
    "ImageWorkspace",
    "OperationLog",
    "install_command",
    "package_for_binary",
    "parse_policy",
    "PlateSolution",
    "load_solution",
    "solution_for_directory",
    "Snapshot",
    "WorkingImage",
    "JobResult",
    "ProcessEngine",
    "ScratchManager",
    "SettingsManager",
]
