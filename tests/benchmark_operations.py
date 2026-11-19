"""Operational benchmark: open, transform and export images up to 10 MP.

Run explicitly with ``python3 tests/benchmark_operations.py`` or through pytest with
``ASTROSTUDIO_BENCHMARK=1``. Results are appended to the persistent operation log.
"""

import os
import shutil
import tempfile
import time

import numpy as np
from gi.repository import GLib
from PIL import Image

from astrostudio.adapters import ImageMagickAdapter
from astrostudio.core import ImageWorkspace, OperationLog, ProcessEngine, ScratchManager
from astrostudio.core.export_formats import find_format

MAX_PIXELS = 10_000_000
CASES = (
    ("small", (640, 480), ("png", "jpg", "tif")),
    ("medium", (1600, 1200), ("png", "tif")),
    ("large", (3200, 2400), ("png",)),
    ("limit-10mp", (4000, 2500), ("png",)),
)
FILTERS = (
    ("resize", {"resize": "50%"}),
    ("unsharp", {"unsharp": "1.5x1+0.7+0.02"}),
    ("blur", {"blur": "0x2"}),
    ("median", {"median": "3"}),
    ("morphology", {"morphology": "Erode Disk:1"}),
)
EXPORTS = (
    ("png8", "png"),
    ("jpg90", "jpg"),
    ("tiff16", "tif"),
    ("fits16", "fits"),
    ("bmp8", "bmp"),
)


def _make_source(directory, name, size, extension):
    path = os.path.join(directory, "%s.%s" % (name, extension))
    generator = np.random.default_rng(1234)
    pixels = generator.integers(0, 256, size=(size[1], size[0], 3), dtype=np.uint8)
    Image.fromarray(pixels, "RGB").save(path)
    return path


def _wait_for(flag, timeout_s=120):
    loop = GLib.MainLoop()
    GLib.timeout_add(int(timeout_s * 1000), loop.quit)
    GLib.timeout_add(20, lambda: loop.quit() if flag else True)
    loop.run()
    return bool(flag)


def _run_case(log, workspace, name, size, extensions, root):
    for extension in extensions:
        if size[0] * size[1] > MAX_PIXELS:
            raise ValueError("benchmark case exceeds 10 megapixels")
        source = _make_source(root, "%s_%s" % (name, extension), size, extension)
        ready = []
        started = time.monotonic()
        workspace.prepare(
            source,
            on_ready=ready.append,
            on_error=lambda message: log.record("benchmark_error", case=name, message=message),
        )
        if not _wait_for(ready):
            log.record("benchmark_timeout", case=name, stage="prepare")
            continue
        image = ready[0]
        log.record(
            "benchmark_case",
            case=name,
            format=extension,
            stage="open",
            width=size[0],
            height=size[1],
            duration_s=round(time.monotonic() - started, 3),
        )

        for filter_name, params in FILTERS:
            done = []
            started = time.monotonic()
            workspace.transform(
                image,
                params,
                on_ready=done.append,
                on_error=lambda message: log.record(
                    "benchmark_error", case=name, message=message
                ),
            )
            if not _wait_for(done):
                log.record("benchmark_timeout", case=name, stage=filter_name)
                continue
            log.record(
                "benchmark_case",
                case=name,
                format=extension,
                stage=filter_name,
                width=size[0],
                height=size[1],
                duration_s=round(time.monotonic() - started, 3),
            )

        for format_key, suffix in EXPORTS:
            destination = os.path.join(
                root, "%s_%s_export.%s" % (name, extension, suffix)
            )
            done = []
            started = time.monotonic()
            workspace.export(
                image,
                destination,
                on_ready=done.append,
                on_error=lambda message: log.record(
                    "benchmark_error", case=name, message=message
                ),
                export_format=find_format(format_key),
            )
            if not _wait_for(done):
                log.record("benchmark_timeout", case=name, stage="export-" + suffix)
                continue
            log.record(
                "benchmark_case",
                case=name,
                format=extension,
                stage="export-" + suffix,
                width=size[0],
                height=size[1],
                output_bytes=os.path.getsize(destination),
                duration_s=round(time.monotonic() - started, 3),
            )
        image = None


def run_benchmark():
    if shutil.which("convert") is None:
        raise RuntimeError("ImageMagick 'convert' is required for the benchmark")
    log = OperationLog()
    log.record("benchmark_start", cases=len(CASES), max_pixels=MAX_PIXELS)
    scratch = ScratchManager("benchmark")
    engine = ProcessEngine(operation_log=log)
    workspace = ImageWorkspace(scratch, engine, ImageMagickAdapter())
    try:
        with tempfile.TemporaryDirectory(prefix="astro_studio_bench_") as root:
            for name, size, extensions in CASES:
                _run_case(log, workspace, name, size, extensions, root)
    finally:
        engine.cancel_all()
        scratch.cleanup_all()
    log.record("benchmark_end")
    return log.entries()


if __name__ == "__main__":
    entries = run_benchmark()
    print("benchmark entries appended:", len(entries))
