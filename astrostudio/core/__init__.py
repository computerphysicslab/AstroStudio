"""Core orchestration components."""

from .astrometry import find_output, find_plate_solution, summarize_solution
from .backends import BackendRegistry, BackendSpec, BackendStatus
from .annotations import Annotation, build_annotate_argv, draw_command
from .bpm import validate_bpm_count
from .wcs import overlay_center, wcs_cards, write_wcs_sidecar
from .calibration import discover_calibration
from .command_builder import CommandBuilder
from .operation_log import OperationLog
from .package_info import install_command, package_for_binary, parse_policy
from .pipeline_export import cli_entries, write_makefile, write_shell
from .presets import parse_metadata_text, suggest_presets
from .provenance import DerivationNode, build_tree, flatten
from .plate_solution import PlateSolution, load_solution, solution_for_directory
from .estimator import Estimator, StageModel
from .frame_quality import FrameDiagnostics, parse_measurements
from .gaia_cache import default_cache_dir, gaia_flags, tile_count
from .linear_guard import check_linear_guard
from .export_formats import EXPORT_FORMATS, ExportFormat, find_format
from .export_paths import unique_export_path
from .histogram import histogram_argv, parse_histogram_text
from .i18n import Translator
from .job_manager import JobManager, JobState
from .image_workspace import ImageWorkspace, Snapshot, WorkingImage
from .process_engine import JobResult, ProcessEngine
from .scratch import ScratchManager
from .session import load_session, save_session
from .settings import SettingsManager

__all__ = [
    "BackendRegistry",
    "BackendSpec",
    "BackendStatus",
    "validate_bpm_count",
    "Annotation",
    "build_annotate_argv",
    "draw_command",
    "wcs_cards",
    "overlay_center",
    "write_wcs_sidecar",
    "CommandBuilder",
    "discover_calibration",
    "FrameDiagnostics",
    "default_cache_dir",
    "gaia_flags",
    "tile_count",
    "check_linear_guard",
    "parse_measurements",
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
    "Translator",
    "JobManager",
    "JobState",
    "unique_export_path",
    "ImageWorkspace",
    "OperationLog",
    "install_command",
    "package_for_binary",
    "parse_policy",
    "parse_metadata_text",
    "suggest_presets",
    "DerivationNode",
    "build_tree",
    "flatten",
    "cli_entries",
    "write_makefile",
    "write_shell",
    "PlateSolution",
    "load_solution",
    "solution_for_directory",
    "Snapshot",
    "WorkingImage",
    "JobResult",
    "ProcessEngine",
    "ScratchManager",
    "load_session",
    "save_session",
    "SettingsManager",
]
