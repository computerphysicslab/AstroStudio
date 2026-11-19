"""Startup discovery of external CLI backends and menu capability gating."""

import re
import shutil
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Sequence, Tuple

from gi.repository import GLib

from .process_engine import JobResult, ProcessEngine

VERSION_RE = re.compile(r"\d+(?:\.\d+){1,3}")


@dataclass(frozen=True)
class BackendSpec:
    name: str
    binary: str
    category: str
    version_args: Tuple[str, ...] = ("--version",)
    alternatives: Tuple[str, ...] = ()


@dataclass
class BackendStatus:
    name: str
    binary: str
    category: str
    available: bool = False
    version: Optional[str] = None
    error: Optional[str] = None

    def label(self) -> Tuple[str, str, str]:
        state = "available" if self.available else "not installed"
        return self.name, state, self.version or "-"


BACKENDS: Tuple[BackendSpec, ...] = (
    BackendSpec("ImageMagick", "magick", "Conversion", ("-version",), ("convert",)),
    BackendSpec("FPack", "fpack", "FITS compression", ("-h",)),
    BackendSpec("gzip", "gzip", "FITS compression", ("--version",)),
    BackendSpec("FFmpeg", "ffmpeg", "Video", ("-version",)),
    BackendSpec("GraphicsMagick", "gm", "Conversion", ("version",)),
    BackendSpec("ExifTool", "exiftool", "Metadata", ("-ver",)),
    BackendSpec("RawTherapee", "rawtherapee-cli", "RAW", ("--version",)),
    BackendSpec("Darktable", "darktable-cli", "RAW", ("--version",)),
    BackendSpec("GIMP", "gimp", "Scripting", ("--version",)),
    BackendSpec("Hugin", "pto_gen", "Alignment", ("--version",)),
    BackendSpec("Enfuse", "enfuse", "Fusion", ("--version",)),
    BackendSpec("LibRaw", "dcraw_emu", "RAW", ("-v",)),
    BackendSpec("PhotoFlow", "photoflow-cli", "Pipelines", ("--version",)),
    BackendSpec("Siril", "siril-cli", "Astronomy", ("--version",)),
    BackendSpec("ASTAP", "astap_cli", "Astronomy", ("--version",)),
    BackendSpec("Astrometry.net", "solve-field", "Astronomy", ("--version",)),
    BackendSpec("SkyStacker", "skystacker", "Astronomy", ("--version",)),
)


ACTION_BACKENDS: Dict[str, Tuple[str, ...]] = {
    "open": (),
    "close": (),
    "close-all": (),
    "quit": (),
    "zoom-in": (),
    "zoom-out": (),
    "zoom-fit": (),
    "undo": (),
    "redo": (),
    "export": ("ImageMagick", "RawTherapee", "Darktable"),
    "export-pipeline": (),
    "export-fits-compressed": ("FPack", "gzip"),
    "inspect-raw": ("ExifTool",),
    "inspect-ser": (),
    "inspect-avi": ("FFmpeg",),
    "save-session": (),
    "resume-session": (),
    "batch": ("GraphicsMagick", "ImageMagick"),
    "resize-10": ("ImageMagick",),
    "resize-25": ("ImageMagick",),
    "resize-50": ("ImageMagick",),
    "resize-75": ("ImageMagick",),
    "resize-100": ("ImageMagick",),
    "resize-150": ("ImageMagick",),
    "resize-200": ("ImageMagick",),
    "resize-400": ("ImageMagick",),
    "resize-1000": ("ImageMagick",),
    "resize-custom": ("ImageMagick",),
    "unsharp": ("ImageMagick",),
    "metadata": ("ExifTool",),
    "select-area": ("ImageMagick",),
    "calibration": ("Siril", "SkyStacker"),
    "stacking": ("Siril", "SkyStacker"),
    "geometry": ("ImageMagick",),
    "derotator": ("Siril",),
    "arithmetic": ("ImageMagick",),
    "color": ("RawTherapee", "Darktable", "ImageMagick"),
    "gradient": ("Siril", "PhotoFlow"),
    "filter": ("ImageMagick", "Siril"),
    "deconvolution": ("Siril", "PhotoFlow"),
    "star-reduction": ("Siril",),
    "histogram": ("ImageMagick",),
    "frame-table": ("SkyStacker",),
    "before-after": ("ImageMagick",),
    "suggest-presets": (),
    "annotations": ("ImageMagick",),
    "wcs-overlay": (),
    "derivation-tree": (),
    "siril-calibrate": ("Siril",),
    "siril-stack": ("Siril",),
    "develop-raw": ("RawTherapee", "Darktable", "LibRaw"),
    "panorama": ("Hugin",),
    "enfuse": ("Enfuse",),
    "gimp-script": ("GIMP",),
    "bpm-auto": ("SkyStacker",),
    "detect-calibration": (),
    "line-profile": ("ImageMagick",),
    "clone-stamp": ("GIMP", "PhotoFlow"),
    "filter-sharpen": ("ImageMagick",),
    "filter-convolve-sharpen": ("ImageMagick",),
    "filter-blur": ("ImageMagick",),
    "filter-gaussian-blur": ("ImageMagick",),
    "filter-median": ("ImageMagick",),
    "filter-despeckle": ("ImageMagick",),
    "filter-adaptive-blur": ("ImageMagick",),
    "filter-convolve-gaussian": ("ImageMagick",),
    "filter-morphology-erode": ("ImageMagick",),
    "filter-edge": ("ImageMagick",),
    "filter-emboss": ("ImageMagick",),
    "filter-star-reduction": ("ImageMagick",),
    "filter-stretch": ("SkyStacker",),
    "plate-solve": ("SkyStacker",),
    "solve-astap": ("ASTAP",),
    "solve-solvefield": ("Astrometry.net",),
    "gaia-cache-info": (),
    "sky-map": ("SkyStacker",),
    "survey-cutout": ("SkyStacker",),
    "about": (),
    "cancel": (),
    "fullscreen": (),
    **{"open-recent-%d" % index: () for index in range(10)},
    "frontend-settings": (),
    "toggle-backends": (),
    "toggle-histogram": (),
    "toggle-terminal": (),
    "settings": (),
    "language": (),
}

IMPLEMENTED_ACTIONS = frozenset(
    {
        "open",
        "close",
        "close-all",
        "quit",
        "zoom-in",
        "zoom-out",
        "zoom-fit",
        "undo",
        "redo",
        "export",
        "export-pipeline",
        "export-fits-compressed",
        "inspect-raw",
        "inspect-ser",
        "inspect-avi",
        "save-session",
        "resume-session",
        "batch",
        "resize-10",
        "resize-25",
        "resize-50",
        "resize-75",
        "resize-100",
        "resize-150",
        "resize-200",
        "resize-400",
        "resize-1000",
        "resize-custom",
        "unsharp",
        "filter-sharpen",
        "filter-convolve-sharpen",
        "filter-blur",
        "filter-gaussian-blur",
        "filter-median",
        "filter-despeckle",
        "filter-adaptive-blur",
        "filter-convolve-gaussian",
        "filter-morphology-erode",
        "filter-edge",
        "filter-emboss",
        "filter-star-reduction",
        "metadata",
        "histogram",
        "frame-table",
        "before-after",
        "suggest-presets",
        "annotations",
        "wcs-overlay",
        "derivation-tree",
        "siril-calibrate",
        "siril-stack",
        "develop-raw",
        "panorama",
        "enfuse",
        "gimp-script",
        "bpm-auto",
        "detect-calibration",
        "select-area",
        "toggle-backends",
        "toggle-histogram",
        "toggle-terminal",
        "plate-solve",
        "solve-astap",
        "solve-solvefield",
        "gaia-cache-info",
        "sky-map",
        "survey-cutout",
        "about",
        "cancel",
        "fullscreen",
        *["open-recent-%d" % index for index in range(10)],
        "frontend-settings",
        "settings",
    }
)


class BackendRegistry:
    """Holds installed/version status for every connector target."""

    def __init__(self, specs: Sequence[BackendSpec] = BACKENDS, settings=None) -> None:
        self.specs = tuple(specs)
        self.settings = settings
        self.status: Dict[str, BackendStatus] = {
            spec.name: BackendStatus(spec.name, spec.binary, spec.category)
            for spec in self.specs
        }
        self._resolve_installed()

    def _resolve_installed(self) -> None:
        for spec in self.specs:
            status = self.status[spec.name]
            resolved = self._resolve_binary(spec)
            status.available = resolved is not None
            status.binary = resolved or spec.binary
            status.error = "not installed" if resolved is None else None

    def _resolve_binary(self, spec: BackendSpec) -> Optional[str]:
        overrides = self.settings.get("binary_overrides", {}) if self.settings else {}
        override = overrides.get(spec.name)
        if override and shutil.which(override):
            return shutil.which(override)
        for candidate in (spec.binary,) + spec.alternatives:
            found = shutil.which(candidate)
            if found:
                return found
        return None

    def probe(
        self,
        engine: ProcessEngine,
        on_update: Optional[Callable[["BackendRegistry"], None]] = None,
    ) -> None:
        for spec in self.specs:
            status = self.status[spec.name]
            if not status.available:
                self._notify(on_update)
                continue
            status.error = None
            status.version = None
            argv = [status.binary] + list(spec.version_args)
            engine.run(
                "probe-" + spec.name,
                argv,
                on_done=lambda result, target=status: self._on_probe(
                    result, target, on_update
                ),
            )

    def _on_probe(
        self,
        result: JobResult,
        status: BackendStatus,
        on_update: Optional[Callable[["BackendRegistry"], None]],
    ) -> None:
        output = "\n".join(part for part in (result.stdout, result.stderr) if part)
        match = VERSION_RE.search(output)
        if match:
            status.version = match.group(0)
        else:
            status.version = "unknown"
            status.error = result.error or "version query failed"
        self._notify(on_update)

    def _notify(self, on_update: Optional[Callable[["BackendRegistry"], None]]) -> None:
        if on_update:
            GLib.idle_add(on_update, self)

    def installed(self, name: str) -> bool:
        status = self.status.get(name)
        return bool(status and status.available)

    def available(self, name: str) -> bool:
        if not self.installed(name):
            return False
        if self.settings is not None and not self.settings.is_backend_enabled(name):
            return False
        return True

    def version(self, name: str) -> Optional[str]:
        status = self.status.get(name)
        return status.version if status else None

    def is_action_enabled(self, action: str) -> bool:
        if action not in IMPLEMENTED_ACTIONS:
            return False
        required = ACTION_BACKENDS.get(action, ())
        return not required or any(self.available(name) for name in required)

    def summary(self) -> List[str]:
        return [
            "%s: %s" % (status.name, status.version or status.error or "unknown")
            for status in self.status.values()
        ]
