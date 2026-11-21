"""Core orchestration components."""

from .astrometry import (
    classify_backend_failure,
    find_output,
    find_plate_solution,
    sky_map_source_count,
    strip_svg_titles,
    summarize_solution,
)
from .backends import BackendRegistry, BackendSpec, BackendStatus
from .annotations import Annotation, build_annotate_argv, draw_command
from .bpm import validate_bpm_count
from .raw_formats import raw_warnings
from .wcs import overlay_center, wcs_cards, write_wcs_sidecar
from .calibration import discover_calibration
from .command_builder import CommandBuilder
from .operation_log import OperationLog
from .plugins import discover_plugins, register_plugins
from .offline_prefetch import DEFAULT_CATALOGS, prefetch_plan
from .package_info import install_command, package_for_binary, parse_policy
from .quality_dashboard import QualityRow, parse_quality_report, summarize
from .pipeline_export import cli_entries, write_makefile, write_shell
from .pipeline_graph import PipelineGraph, PipelineNode
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
from .hot_folder import HotFolderWatcher, folders_from_files
from .i18n import Translator
from .job_manager import JobManager, JobState
from .image_workspace import ImageWorkspace, Snapshot, WorkingImage
from .fits_hdus import FitsHdu, inspect_fits
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
from .preview_pyramid import PYRAMID_LEVELS, choose_level, pyramid_paths
from .scratch import ScratchManager
from .session import load_session, save_session
from .structured_log import CallbackHandler, StructuredLogger
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
    "classify_backend_failure",
    "find_output",
    "find_plate_solution",
    "sky_map_source_count",
    "strip_svg_titles",
    "summarize_solution",
    "EXPORT_FORMATS",
    "ExportFormat",
    "Estimator",
    "StageModel",
    "QualityRow",
    "parse_quality_report",
    "summarize",
    "find_format",
    "histogram_argv",
    "HotFolderWatcher",
    "folders_from_files",
    "parse_histogram_text",
    "Translator",
    "JobManager",
    "JobState",
    "unique_export_path",
    "ImageWorkspace",
    "FitsHdu",
    "inspect_fits",
    "Hint",
    "extract_tokens",
    "load_catalog",
    "plate_center_argv",
    "resolve_filename",
    "unique_hint",
    "OperationLog",
    "discover_plugins",
    "register_plugins",
    "DEFAULT_CATALOGS",
    "prefetch_plan",
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
    "PipelineGraph",
    "PipelineNode",
    "write_shell",
    "PlateSolution",
    "load_solution",
    "solution_for_directory",
    "Snapshot",
    "WorkingImage",
    "JobResult",
    "ProcessEngine",
    "PYRAMID_LEVELS",
    "choose_level",
    "pyramid_paths",
    "ScratchManager",
    "load_session",
    "save_session",
    "StructuredLogger",
    "CallbackHandler",
    "StarDetection",
    "parse_star_catalog",
    "star_display_radius",
    "write_star_layer_svg",
    "SettingsManager",
    "SKY_FILTERS",
    "SKY_FILTER_MENU",
]
