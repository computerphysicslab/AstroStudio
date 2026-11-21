"""Dual-format working image store: high-depth TIFF plus display PNG.

Every image kept by the GUI has two artifacts in scratch: a 16-bit TIFF used as
the sole input for external CLI transformations, and an 8-bit PNG generated from
that TIFF and used only for on-screen rendering. Transformations replace the
TIFF, then regenerate the PNG. No pixel processing happens in this module.
"""

import hashlib
import json
import os
import shutil
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Sequence, Tuple

if TYPE_CHECKING:
    from ..adapters import ImageMagickAdapter, SkyStackerAdapter
    from .export_formats import ExportFormat

from .process_engine import JobResult, ProcessEngine
from .scratch import ScratchManager

ReadyCallback = Callable[["WorkingImage"], None]
ErrorCallback = Callable[[str], None]
LogCallback = Callable[[str], None]


@dataclass
class Snapshot:
    tiff_path: str
    png_path: str


@dataclass
class WorkingImage:
    key: str
    source: str
    directory: str
    tiff_path: str
    png_path: str
    display_stretch: bool = False
    stretch_points: Optional[Tuple[float, float]] = None
    gamma: Optional[float] = None


class ImageWorkspace:
    def __init__(
        self,
        scratch: ScratchManager,
        engine: ProcessEngine,
        adapter: "ImageMagickAdapter" = None,
        cache_dir: str = None,
        history_depth: int = 10,
    ) -> None:
        if adapter is None:
            from ..adapters.magick import ImageMagickAdapter

            adapter = ImageMagickAdapter()
        self.scratch = scratch
        self.engine = engine
        self.adapter = adapter
        self.cache_dir = cache_dir
        self.history_depth = max(1, int(history_depth))
        if self.cache_dir:
            os.makedirs(self.cache_dir, exist_ok=True)
        self.images: Dict[str, WorkingImage] = {}
        self._undo: Dict[str, List[Snapshot]] = {}
        self._redo: Dict[str, List[Snapshot]] = {}
        self._snapshot_counter: Dict[str, int] = {}
        self._pyramids: Dict[str, List[Tuple[str, float]]] = {}
        self._counter = 0

    def ensure_pyramid(
        self,
        image: WorkingImage,
        on_ready: Callable[[List[Tuple[str, float]]], None],
        on_error: ErrorCallback,
        on_log: Optional[LogCallback] = None,
    ) -> None:
        """Generate downscaled preview levels with external CLI jobs."""
        from .preview_pyramid import PYRAMID_LEVELS, pyramid_paths

        missing = [
            (name, scale)
            for name, scale in PYRAMID_LEVELS
            if not os.path.isfile(os.path.join(image.directory, name))
        ]
        if not missing:
            levels = pyramid_paths(image.directory)
            self._pyramids[image.key] = levels
            on_ready(levels)
            return
        self._run_pyramid_job(image, missing, 0, on_ready, on_error, on_log)

    def _run_pyramid_job(
        self,
        image: WorkingImage,
        jobs: List[Tuple[str, float]],
        index: int,
        on_ready: Callable[[List[Tuple[str, float]]], None],
        on_error: ErrorCallback,
        on_log: Optional[LogCallback],
    ) -> None:
        from .preview_pyramid import pyramid_paths

        if index >= len(jobs):
            levels = pyramid_paths(image.directory)
            self._pyramids[image.key] = levels
            on_ready(levels)
            return
        builder = getattr(self.adapter, "build_pyramid_argv", None)
        if builder is None:
            if on_log:
                on_log("Preview pyramid unsupported by %s" % type(self.adapter).__name__)
            self._pyramids[image.key] = []
            on_ready([])
            return
        name, scale = jobs[index]
        destination = os.path.join(image.directory, name)
        argv = builder(
            image.tiff_path,
            destination,
            scale,
            image.display_stretch,
            image.stretch_points,
            image.gamma,
        )
        if on_log:
            on_log("Preview pyramid level: %s" % " ".join(argv))
        self.engine.run(
            image.key + "-pyramid-%d" % index,
            argv,
            on_log=on_log,
            on_done=lambda result: self._on_pyramid_job(
                result, image, jobs, index, on_ready, on_error, on_log
            ),
        )

    def _on_pyramid_job(
        self,
        result: JobResult,
        image: WorkingImage,
        jobs: List[Tuple[str, float]],
        index: int,
        on_ready: Callable[[List[Tuple[str, float]]], None],
        on_error: ErrorCallback,
        on_log: Optional[LogCallback],
    ) -> None:
        if not result.ok:
            self._fail(
                "Preview pyramid failed: %s" % (result.error or result.stderr),
                on_error,
                on_log,
            )
            return
        self._run_pyramid_job(image, jobs, index + 1, on_ready, on_error, on_log)

    def prepare(
        self,
        source: str,
        on_ready: ReadyCallback,
        on_error: ErrorCallback,
        on_log: Optional[LogCallback] = None,
        display_stretch: Optional[bool] = None,
    ) -> WorkingImage:
        self._counter += 1
        key = "image-%04d" % self._counter
        directory = self.scratch.job_dir(key)
        auto_stretch = source.lower().endswith(
            (
                ".fits",
                ".fit",
                ".fts",
                ".cr2",
                ".cr3",
                ".nef",
                ".arw",
                ".dng",
                ".psd",
                ".psb",
            )
        )
        if display_stretch is None:
            display_stretch = auto_stretch
        image = WorkingImage(
            key=key,
            source=source,
            directory=directory,
            tiff_path=os.path.join(directory, "working.tiff"),
            png_path=os.path.join(directory, "preview.png"),
            display_stretch=display_stretch,
        )
        self.images[key] = image

        if source.lower().endswith((".fits", ".fit", ".fts")):
            from .fits_hdus import inspect_fits

            layout = inspect_fits(source)
            if layout["error"]:
                self._fail(
                    "FITS import rejected for %s: %s" % (os.path.basename(source), layout["error"]),
                    on_error,
                    on_log,
                )
                return image

        if source.lower().endswith(".cr2"):
            from ..adapters.skystacker import SkyStackerAdapter

            raw_adapter = SkyStackerAdapter()
            raw_input = os.path.join(directory, "raw_input")
            raw_output = os.path.join(directory, "raw_stack")
            os.makedirs(raw_input, exist_ok=True)
            shutil.copy2(source, os.path.join(raw_input, os.path.basename(source)))
            argv = raw_adapter.build_raw_import_argv(raw_input, raw_output)
            if on_log:
                on_log("CR2 native decode: %s" % " ".join(argv))
            self.engine.run(
                key + "-raw-import",
                argv,
                on_log=on_log,
                on_done=lambda result: self._on_raw_import(
                    result, image, raw_output, on_ready, on_error, on_log
                ),
            )
            return image

        import_argv = self.adapter.build_import_argv(source, image.tiff_path)
        if on_log:
            on_log("Import to 16-bit TIFF: %s" % " ".join(import_argv))
        self.engine.run(
            key + "-import",
            import_argv,
            on_log=on_log,
            on_done=lambda result: self._on_import(
                result, image, on_ready, on_error, on_log
            ),
        )
        return image

    def _on_import(
        self,
        result: JobResult,
        image: WorkingImage,
        on_ready: ReadyCallback,
        on_error: ErrorCallback,
        on_log: Optional[LogCallback],
    ) -> None:
        if not result.ok:
            self._fail("TIFF import failed for %s: %s" % (image.source, result.error or result.stderr), on_error, on_log)
            return
        if on_log:
            on_log("CLI %s exit %d" % (result.job_id, result.exit_code))
        self._make_preview(image, on_ready, on_error, on_log)

    def _on_raw_import(
        self,
        result: JobResult,
        image: WorkingImage,
        output_dir: str,
        on_ready: ReadyCallback,
        on_error: ErrorCallback,
        on_log: Optional[LogCallback],
    ) -> None:
        if not result.ok:
            self._fail("CR2 decode failed: %s" % (result.error or result.stderr), on_error, on_log)
            return
        produced = os.path.join(output_dir, "TIFF", "stacked_sum.tif")
        if not os.path.isfile(produced):
            for root, _dirs, files in os.walk(output_dir):
                for name in sorted(files):
                    if name.lower().endswith((".tif", ".tiff")):
                        produced = os.path.join(root, name)
                        break
        if not os.path.isfile(produced):
            self._fail("CR2 decode produced no TIFF", on_error, on_log)
            return
        shutil.copyfile(produced, image.tiff_path)
        if on_log:
            on_log("CLI %s exit %d; float TIFF ready" % (result.job_id, result.exit_code))
        self._make_preview(image, on_ready, on_error, on_log)

    def _make_preview(
        self,
        image: WorkingImage,
        on_ready: ReadyCallback,
        on_error: ErrorCallback,
        on_log: Optional[LogCallback],
    ) -> None:
        temporary_png = image.png_path + ".next"
        argv = self.adapter.build_preview_argv(
            image.tiff_path,
            temporary_png,
            image.display_stretch,
            image.stretch_points,
            image.gamma,
        )
        if on_log:
            on_log("Preview PNG from TIFF: %s" % " ".join(argv))
        self.engine.run(
            image.key + "-preview",
            argv,
            on_log=on_log,
            on_done=lambda result: self._on_preview(
                result, image, on_ready, on_error, on_log
            ),
        )

    def _on_preview(
        self,
        result: JobResult,
        image: WorkingImage,
        on_ready: ReadyCallback,
        on_error: ErrorCallback,
        on_log: Optional[LogCallback],
    ) -> None:
        if not result.ok:
            self._fail("PNG preview failed: %s" % (result.error or result.stderr), on_error, on_log)
            return
        os.replace(image.png_path + ".next", image.png_path)
        if on_log:
            on_log("CLI %s exit %d" % (result.job_id, result.exit_code))
        on_ready(image)

    def update_preview(
        self,
        image: WorkingImage,
        on_ready: ReadyCallback,
        on_error: ErrorCallback,
        on_log: Optional[LogCallback] = None,
    ) -> None:
        """Regenerate only the display PNG, keeping the high-depth TIFF intact."""
        self._make_preview(image, on_ready, on_error, on_log)

    def transform(
        self,
        image: WorkingImage,
        params: Dict[str, Any],
        on_ready: ReadyCallback,
        on_error: ErrorCallback,
        on_log: Optional[LogCallback] = None,
    ) -> None:
        next_tiff = os.path.join(image.directory, "working_next.tiff")
        argv = self.adapter.build_argv([image.tiff_path], next_tiff, params)
        cached = self._cached_artifact(image.tiff_path, argv)
        self._snapshot(image, self._undo)
        self._redo[image.key] = []
        if cached:
            shutil.copyfile(cached, next_tiff)
            if on_log:
                on_log("Cache hit for transform: %s" % os.path.basename(cached))
            self._finish_transform(image, next_tiff, on_ready, on_error, on_log)
            return
        if on_log:
            on_log("CLI transform on TIFF: %s" % " ".join(argv))
        self.engine.run(
            image.key + "-transform",
            argv,
            on_log=on_log,
            on_done=lambda result: self._on_transform(
                result, image, next_tiff, argv, on_ready, on_error, on_log
            ),
        )

    def transform_via_image_op(
        self,
        image: WorkingImage,
        sky_adapter: "SkyStackerAdapter",
        image_op: str,
        flags: List[str],
        on_ready: ReadyCallback,
        on_error: ErrorCallback,
        on_log: Optional[LogCallback] = None,
    ) -> None:
        """Apply a SkyStacker image-op directly to the working TIFF.

        SkyStacker decodes 8/16-bit and float TIFF through its first-party goTiff
        reader, so no intermediate PNG is needed. The image-op JPEG product is
        converted back to a 16-bit TIFF before the standard commit/preview step.
        """
        output_dir = os.path.join(image.directory, "sky_" + image_op)
        next_tiff = os.path.join(image.directory, "working_next.tiff")
        self._snapshot(image, self._undo)
        self._redo[image.key] = []
        argv = sky_adapter.build_image_op_argv(image.tiff_path, output_dir, image_op, flags)
        if on_log:
            on_log("CLI SkyStacker image-op: %s" % " ".join(argv))
        self.engine.run(
            image.key + "-sky-" + image_op,
            argv,
            on_log=on_log,
            on_done=lambda sky_result: self._on_sky_image_op(
                sky_result, image, sky_adapter, image_op, output_dir, next_tiff,
                on_ready, on_error, on_log
            ),
        )

    def _on_sky_image_op(
        self,
        result: JobResult,
        image: WorkingImage,
        sky_adapter: "SkyStackerAdapter",
        image_op: str,
        output_dir: str,
        next_tiff: str,
        on_ready: ReadyCallback,
        on_error: ErrorCallback,
        on_log: Optional[LogCallback],
    ) -> None:
        if not result.ok:
            self._fail("SkyStacker image-op failed: %s" % (result.error or result.stderr), on_error, on_log)
            return
        product = sky_adapter.find_image_product(output_dir, image_op)
        if not product:
            self._fail("SkyStacker image-op produced no image", on_error, on_log)
            return
        argv = self.adapter.build_import_argv(product, next_tiff)
        if on_log:
            on_log("SkyStacker product to TIFF: %s" % " ".join(argv))
        self.engine.run(
            image.key + "-sky-tiff",
            argv,
            on_log=on_log,
            on_done=lambda tiff_result: self._on_sky_tiff(
                tiff_result, image, next_tiff, on_ready, on_error, on_log
            ),
        )

    def _on_sky_tiff(
        self,
        result: JobResult,
        image: WorkingImage,
        next_tiff: str,
        on_ready: ReadyCallback,
        on_error: ErrorCallback,
        on_log: Optional[LogCallback],
    ) -> None:
        if not result.ok:
            self._fail("SkyStacker TIFF import failed: %s" % (result.error or result.stderr), on_error, on_log)
            return
        self._finish_transform(image, next_tiff, on_ready, on_error, on_log)

    def _cache_path(self, source_tiff: str, argv: List[str]) -> str:
        if not self.cache_dir:
            return ""
        digest = hashlib.sha256()
        with open(source_tiff, "rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        digest.update(json.dumps(argv, sort_keys=True).encode("utf-8"))
        return os.path.join(self.cache_dir, digest.hexdigest() + ".tiff")

    def _cached_artifact(self, source_tiff: str, argv: List[str]) -> str:
        if not self.cache_dir or not os.path.isfile(source_tiff):
            return ""
        path = self._cache_path(source_tiff, argv)
        return path if os.path.isfile(path) else ""

    def _finish_transform(
        self,
        image: WorkingImage,
        next_tiff: str,
        on_ready: ReadyCallback,
        on_error: ErrorCallback,
        on_log: Optional[LogCallback],
    ) -> None:
        os.replace(next_tiff, image.tiff_path)
        if on_log:
            on_log("Replaced working TIFF: %s" % image.tiff_path)
        self._make_preview(image, on_ready, on_error, on_log)

    def _on_transform(
        self,
        result: JobResult,
        image: WorkingImage,
        next_tiff: str,
        argv: List[str],
        on_ready: ReadyCallback,
        on_error: ErrorCallback,
        on_log: Optional[LogCallback],
    ) -> None:
        if not result.ok:
            self._fail("TIFF transform failed: %s" % (result.error or result.stderr), on_error, on_log)
            return
        if on_log:
            on_log("CLI %s exit %d" % (result.job_id, result.exit_code))
        if self.cache_dir and os.path.isfile(next_tiff):
            try:
                shutil.copyfile(next_tiff, self._cache_path(image.tiff_path, argv))
            except OSError:
                pass
        self._finish_transform(image, next_tiff, on_ready, on_error, on_log)

    def export(
        self,
        image: WorkingImage,
        destination: str,
        on_ready: Callable[[str], None],
        on_error: ErrorCallback,
        on_log: Optional[LogCallback] = None,
        export_format: "ExportFormat" = None,
    ) -> None:
        if export_format is not None and export_format.key == "png8":
            shutil.copyfile(image.png_path, destination)
            on_ready(destination)
            return
        if export_format is not None and export_format.category == "Display":
            argv = self.adapter.build_display_export_argv(
                image.tiff_path,
                destination,
                export_format,
                image.gamma,
                image.stretch_points,
            )
        else:
            argv = self.adapter.build_export_argv(
                image.tiff_path, destination, export_format
            )
        if on_log:
            on_log("Export from TIFF: %s" % " ".join(argv))
        self.engine.run(
            image.key + "-export",
            argv,
            on_log=on_log,
            on_done=lambda result: self._on_export(result, destination, on_ready, on_error, on_log),
        )

    def _on_export(
        self,
        result: JobResult,
        destination: str,
        on_ready: Callable[[str], None],
        on_error: ErrorCallback,
        on_log: Optional[LogCallback],
    ) -> None:
        if not result.ok:
            self._fail("Export failed: %s" % (result.error or result.stderr), on_error, on_log)
            return
        if on_log:
            on_log("CLI %s exit %d" % (result.job_id, result.exit_code))
        on_ready(destination)

    def _snapshot(
        self, image: WorkingImage, stack: Dict[str, List[Snapshot]]
    ) -> Snapshot:
        count = self._snapshot_counter.get(image.key, 0) + 1
        self._snapshot_counter[image.key] = count
        snapshot = Snapshot(
            tiff_path=os.path.join(image.directory, "snapshot_%03d.tiff" % count),
            png_path=os.path.join(image.directory, "snapshot_%03d.png" % count),
        )
        self._link_or_copy(image.tiff_path, snapshot.tiff_path)
        self._link_or_copy(image.png_path, snapshot.png_path)
        entries = stack.setdefault(image.key, [])
        entries.append(snapshot)
        while len(entries) > self.history_depth:
            old = entries.pop(0)
            for path in (old.tiff_path, old.png_path):
                try:
                    os.unlink(path)
                except OSError:
                    pass
        return snapshot

    @staticmethod
    def _link_or_copy(source: str, destination: str) -> None:
        try:
            os.link(source, destination)
        except OSError:
            shutil.copyfile(source, destination)

    @staticmethod
    def _restore(source: str, destination: str) -> None:
        temporary = destination + ".restore"
        try:
            os.link(source, temporary)
        except OSError:
            shutil.copyfile(source, temporary)
        os.replace(temporary, destination)

    def can_undo(self, image: WorkingImage) -> bool:
        return bool(self._undo.get(image.key))

    def can_redo(self, image: WorkingImage) -> bool:
        return bool(self._redo.get(image.key))

    def undo(
        self,
        image: WorkingImage,
        on_ready: ReadyCallback,
        on_error: ErrorCallback,
        on_log: Optional[LogCallback] = None,
    ) -> None:
        stack = self._undo.get(image.key, [])
        if not stack:
            on_error("Nothing to undo")
            return
        self._snapshot(image, self._redo)
        snapshot = stack.pop()
        self._restore(snapshot.tiff_path, image.tiff_path)
        self._restore(snapshot.png_path, image.png_path)
        if on_log:
            on_log("Undo restored TIFF/PNG for %s" % image.key)
        on_ready(image)

    def redo(
        self,
        image: WorkingImage,
        on_ready: ReadyCallback,
        on_error: ErrorCallback,
        on_log: Optional[LogCallback] = None,
    ) -> None:
        stack = self._redo.get(image.key, [])
        if not stack:
            on_error("Nothing to redo")
            return
        self._snapshot(image, self._undo)
        snapshot = stack.pop()
        self._restore(snapshot.tiff_path, image.tiff_path)
        self._restore(snapshot.png_path, image.png_path)
        if on_log:
            on_log("Redo restored TIFF/PNG for %s" % image.key)
        on_ready(image)

    @staticmethod
    def _fail(message: str, on_error: ErrorCallback, on_log: Optional[LogCallback]) -> None:
        if on_log:
            on_log(message)
        on_error(message)
