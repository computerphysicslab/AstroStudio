"""Dual-format working image store: high-depth TIFF plus display PNG.

Every image kept by the GUI has two artifacts in scratch: a 16-bit TIFF used as
the sole input for external CLI transformations, and an 8-bit PNG generated from
that TIFF and used only for on-screen rendering. Transformations replace the
TIFF, then regenerate the PNG. No pixel processing happens in this module.
"""

import os
import shutil
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from ..adapters import ImageMagickAdapter
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
    stretch_points: tuple = None


class ImageWorkspace:
    def __init__(
        self,
        scratch: ScratchManager,
        engine: ProcessEngine,
        adapter: "ImageMagickAdapter" = None,
    ) -> None:
        if adapter is None:
            from ..adapters.magick import ImageMagickAdapter

            adapter = ImageMagickAdapter()
        self.scratch = scratch
        self.engine = engine
        self.adapter = adapter
        self.images: Dict[str, WorkingImage] = {}
        self._undo: Dict[str, List[Snapshot]] = {}
        self._redo: Dict[str, List[Snapshot]] = {}
        self._snapshot_counter: Dict[str, int] = {}
        self._counter = 0

    def prepare(
        self,
        source: str,
        on_ready: ReadyCallback,
        on_error: ErrorCallback,
        on_log: Optional[LogCallback] = None,
    ) -> WorkingImage:
        self._counter += 1
        key = "image-%04d" % self._counter
        directory = self.scratch.job_dir(key)
        display_stretch = source.lower().endswith(
            (".fits", ".fit", ".fts", ".cr2", ".cr3", ".nef", ".arw", ".dng")
        )
        image = WorkingImage(
            key=key,
            source=source,
            directory=directory,
            tiff_path=os.path.join(directory, "working.tiff"),
            png_path=os.path.join(directory, "preview.png"),
            display_stretch=display_stretch,
        )
        self.images[key] = image
        argv = self.adapter.build_import_argv(source, image.tiff_path)
        if on_log:
            on_log("Import to 16-bit TIFF: %s" % " ".join(argv))
        self.engine.run(
            key + "-import",
            argv,
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

    def _make_preview(
        self,
        image: WorkingImage,
        on_ready: ReadyCallback,
        on_error: ErrorCallback,
        on_log: Optional[LogCallback],
    ) -> None:
        argv = self.adapter.build_preview_argv(
            image.tiff_path,
            image.png_path,
            image.display_stretch,
            image.stretch_points,
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
        self._snapshot(image, self._undo)
        self._redo[image.key] = []
        next_tiff = os.path.join(image.directory, "working_next.tiff")
        argv = self.adapter.build_argv([image.tiff_path], next_tiff, params)
        if on_log:
            on_log("CLI transform on TIFF: %s" % " ".join(argv))
        self.engine.run(
            image.key + "-transform",
            argv,
            on_log=on_log,
            on_done=lambda result: self._on_transform(
                result, image, next_tiff, on_ready, on_error, on_log
            ),
        )

    def _on_transform(
        self,
        result: JobResult,
        image: WorkingImage,
        next_tiff: str,
        on_ready: ReadyCallback,
        on_error: ErrorCallback,
        on_log: Optional[LogCallback],
    ) -> None:
        if not result.ok:
            self._fail("TIFF transform failed: %s" % (result.error or result.stderr), on_error, on_log)
            return
        if on_log:
            on_log("CLI %s exit %d" % (result.job_id, result.exit_code))
        os.replace(next_tiff, image.tiff_path)
        if on_log:
            on_log("Replaced working TIFF: %s" % image.tiff_path)
        self._make_preview(image, on_ready, on_error, on_log)

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
        shutil.copyfile(image.tiff_path, snapshot.tiff_path)
        shutil.copyfile(image.png_path, snapshot.png_path)
        stack.setdefault(image.key, []).append(snapshot)
        return snapshot

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
        shutil.copyfile(snapshot.tiff_path, image.tiff_path)
        shutil.copyfile(snapshot.png_path, image.png_path)
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
        shutil.copyfile(snapshot.tiff_path, image.tiff_path)
        shutil.copyfile(snapshot.png_path, image.png_path)
        if on_log:
            on_log("Redo restored TIFF/PNG for %s" % image.key)
        on_ready(image)

    @staticmethod
    def _fail(message: str, on_error: ErrorCallback, on_log: Optional[LogCallback]) -> None:
        if on_log:
            on_log(message)
        on_error(message)
