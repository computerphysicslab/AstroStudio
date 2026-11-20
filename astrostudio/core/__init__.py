"""Core orchestration components."""

from .astrometry import find_output, find_plate_solution, summarize_solution
from .backends import BackendRegistry, BackendSpec, BackendStatus
from .annotations import Annotation, build_annotate_argv, draw_command
from .bpm import validate_bpm_count
from .raw_formats import raw_warnings
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
from .catalog_hints import (
    Hint,
    extract_tokens,
    load_catalog,
    plate_center_argv,
    resolve_filename,
    unique_hint,
)
from .object_classification import (
    DiffuseObject,
    parse_classification,
    write_object_layer_svg,
)
from .process_engine import JobResult, ProcessEngine
from .scratch import ScratchManager
from .session import load_session, save_session
from .star_catalog import (
    StarDetection,
    parse_star_catalog,
    star_display_radius,
    write_star_layer_svg,
)
from .video import (
    SerHeader,
    ffmpeg_extract_argv,
    parse_ser_header,
    validate_avi_codec,
)
from .settings import SettingsManager
from .sky_filters import SKY_FILTERS, SKY_FILTER_MENU

__all__ = [
    "BackendRegistry",
    "BackendSpec",
    "BackendStatus",
    "validate_bpm_count",
    "raw_warnings",
    "SerHeader",
    "ffmpeg_extract_argv",
    "parse_ser_header",
    "validate_avi_codec",
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
    "Hint",
    "extract_tokens",
    "load_catalog",
    "plate_center_argv",
    "resolve_filename",
    "unique_hint",
    "OperationLog",
    "DiffuseObject",
    "parse_classification",
    "write_object_layer_svg",
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
    "StarDetection",
    "parse_star_catalog",
    "star_display_radius",
    "write_star_layer_svg",
    "SettingsManager",
    "SKY_FILTERS",
    "SKY_FILTER_MENU",
]
