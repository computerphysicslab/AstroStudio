"""Dual-format TIFF/PNG workspace tests."""

import os
from pathlib import Path

import pytest

from astrostudio.adapters import ImageMagickAdapter
from astrostudio.core import ImageWorkspace, ScratchManager
from astrostudio.core.export_formats import find_format
from astrostudio.core.process_engine import JobResult


def _output_path(argv):
    output = argv[-1]
    return output[4:] if output.startswith("png:") else output


class FakeEngine:
    def __init__(self, fail_on=None):
        self.calls = []
        self.fail_on = fail_on

    def run(self, job_id, argv, on_log=None, on_done=None):
        self.calls.append((job_id, list(argv)))
        if self.fail_on and job_id.endswith(self.fail_on):
            on_done(JobResult(job_id=job_id, argv=list(argv), exit_code=1, stderr="boom"))
            return
        Path(_output_path(argv)).write_bytes(("data:" + job_id).encode())
        on_done(JobResult(job_id=job_id, argv=list(argv), exit_code=0))


def header_bytes(cards):
    return "".join(card.ljust(80) for card in cards).encode("ascii").ljust(2880, b" ")


def _workspace(tmp_path, monkeypatch, engine, history_depth=10):
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    (tmp_path / "runtime").mkdir()
    return ImageWorkspace(
        ScratchManager("session"),
        engine,
        ImageMagickAdapter(binary="convert"),
        history_depth=history_depth,
    )


def test_prepare_creates_tiff_and_png_without_touching_source(tmp_path, monkeypatch):
    engine = FakeEngine()
    workspace = _workspace(tmp_path, monkeypatch, engine)
    source = tmp_path / "original.png"
    source.write_bytes(b"original")
    ready = []

    image = workspace.prepare(
        str(source), ready.append, lambda message: pytest.fail(message)
    )

    assert len(engine.calls) == 2
    assert engine.calls[0][0] == "image-0001-import"
    assert engine.calls[0][1][0] == "convert"
    assert "-depth" in engine.calls[0][1] and "16" in engine.calls[0][1]
    assert engine.calls[1][0] == "image-0001-preview-1"
    assert "-depth" in engine.calls[1][1] and "8" in engine.calls[1][1]
    assert ready == [image]
    assert Path(image.tiff_path).read_bytes() == b"data:image-0001-import"
    assert Path(image.png_path).read_bytes() == b"data:image-0001-preview-1"
    assert source.read_bytes() == b"original"


def test_transform_replaces_tiff_and_regenerates_png(tmp_path, monkeypatch):
    engine = FakeEngine()
    workspace = _workspace(tmp_path, monkeypatch, engine)
    source = tmp_path / "source.png"
    source.write_bytes(b"source")
    image = workspace.prepare(str(source), lambda *_: None, lambda message: pytest.fail(message))
    ready = []

    workspace.transform(
        image, {"resize": "50%"}, ready.append, lambda message: pytest.fail(message)
    )

    assert engine.calls[-2][0] == "image-0001-transform"
    assert engine.calls[-2][1][1] == image.tiff_path
    assert engine.calls[-2][1][-1].endswith("working_next.tiff")
    assert "-resize" in engine.calls[-2][1]
    assert "50%" in engine.calls[-2][1]
    assert engine.calls[-1][0].startswith("image-0001-preview-")
    assert ready == [image]
    assert Path(image.tiff_path).read_bytes() == b"data:image-0001-transform"
    assert Path(image.png_path).read_bytes() == b"data:image-0001-preview-2"
    assert not os.path.exists(os.path.join(image.directory, "working_next.tiff"))


def test_fits_source_combines_hdus_and_uses_display_stretch(tmp_path, monkeypatch):
    engine = FakeEngine()
    workspace = _workspace(tmp_path, monkeypatch, engine)
    source = tmp_path / "light.fits"
    cards = [
        "SIMPLE  =                    T",
        "BITPIX  =                   16",
        "NAXIS   =                    2",
        "NAXIS1  =                   16",
        "NAXIS2  =                   16",
        "END",
    ]
    header = "".join(card.ljust(80) for card in cards).encode("ascii")
    source.write_bytes(header.ljust(2880, b" "))

    image = workspace.prepare(str(source), lambda *_: None, lambda message: pytest.fail(message))

    assert image.display_stretch
    assert "-combine" in engine.calls[0][1]
    assert "-evaluate" in engine.calls[1][1]
    assert "0.45" in engine.calls[1][1]


def test_cr2_prepare_uses_skystacker_float_tiff(tmp_path, monkeypatch):
    class RawEngine(FakeEngine):
        def run(self, job_id, argv, on_log=None, on_done=None):
            if "raw-import" in job_id:
                self.calls.append((job_id, list(argv)))
                output_dir = argv[argv.index("--output") + 1]
                produced = Path(output_dir) / "TIFF" / "stacked_sum.tif"
                produced.parent.mkdir(parents=True, exist_ok=True)
                produced.write_bytes(b"float-tiff")
                on_done(JobResult(job_id=job_id, argv=list(argv), exit_code=0))
                return
            super().run(job_id, argv, on_log, on_done)

    engine = RawEngine()
    workspace = _workspace(tmp_path, monkeypatch, engine)
    source = tmp_path / "light.CR2"
    source.write_bytes(b"cr2")

    ready = []
    image = workspace.prepare(str(source), ready.append, lambda message: pytest.fail(message))

    assert ready == [image]
    assert image.display_stretch
    assert Path(image.tiff_path).read_bytes() == b"float-tiff"
    assert any("raw-import" in call[0] for call in engine.calls)
    assert "-evaluate" in engine.calls[-1][1]


def test_update_preview_regenerates_png_with_stretch_points(tmp_path, monkeypatch):
    engine = FakeEngine()
    workspace = _workspace(tmp_path, monkeypatch, engine)
    source = tmp_path / "source.png"
    source.write_bytes(b"source")
    image = workspace.prepare(str(source), lambda *_: None, lambda message: pytest.fail(message))
    image.stretch_points = (25.5, 204.0)

    workspace.update_preview(image, lambda *_: None, lambda message: pytest.fail(message))

    assert "-level" in engine.calls[-1][1]
    assert "10.0%,80.0%" in engine.calls[-1][1]
    assert "-resize" not in engine.calls[-1][1]


def test_content_hash_cache_reuses_transform(tmp_path, monkeypatch):
    engine = FakeEngine()
    workspace = _workspace(tmp_path, monkeypatch, engine)
    workspace.cache_dir = str(tmp_path / "cache")
    Path(workspace.cache_dir).mkdir()
    source = tmp_path / "source.png"
    source.write_bytes(b"source")
    image = workspace.prepare(str(source), lambda *_: None, lambda message: pytest.fail(message))
    original = Path(image.tiff_path).read_bytes()

    workspace.transform(image, {"resize": "50%"}, lambda *_: None, lambda message: pytest.fail(message))
    first_count = len([c for c in engine.calls if "transform" in c[0]])
    Path(image.tiff_path).write_bytes(original)

    workspace.transform(image, {"resize": "50%"}, lambda *_: None, lambda message: pytest.fail(message))
    second_count = len([c for c in engine.calls if "transform" in c[0]])
    assert first_count == 1
    assert second_count == 1


def test_undo_and_redo_restore_both_artifacts(tmp_path, monkeypatch):
    engine = FakeEngine()
    workspace = _workspace(tmp_path, monkeypatch, engine)
    source = tmp_path / "source.png"
    source.write_bytes(b"source")
    image = workspace.prepare(str(source), lambda *_: None, lambda message: pytest.fail(message))
    original_tiff = Path(image.tiff_path).read_bytes()
    original_png = Path(image.png_path).read_bytes()

    workspace.transform(image, {"resize": "50%"}, lambda *_: None, lambda message: pytest.fail(message))
    transformed_tiff = Path(image.tiff_path).read_bytes()
    assert transformed_tiff != original_tiff
    assert workspace.can_undo(image)
    assert not workspace.can_redo(image)

    workspace.undo(image, lambda *_: None, lambda message: pytest.fail(message))
    assert Path(image.tiff_path).read_bytes() == original_tiff
    assert Path(image.png_path).read_bytes() == original_png
    assert workspace.can_redo(image)

    workspace.redo(image, lambda *_: None, lambda message: pytest.fail(message))
    assert Path(image.tiff_path).read_bytes() == transformed_tiff
    assert Path(image.png_path).read_bytes() == b"data:image-0001-preview-2"


def test_export_uses_png_copy_or_tiff_cli(tmp_path, monkeypatch):
    engine = FakeEngine()
    workspace = _workspace(tmp_path, monkeypatch, engine)
    source = tmp_path / "source.png"
    source.write_bytes(b"source")
    image = workspace.prepare(str(source), lambda *_: None, lambda message: pytest.fail(message))

    png_destination = tmp_path / "copy.png"
    exported = []
    workspace.export(
        image,
        str(png_destination),
        exported.append,
        lambda message: pytest.fail(message),
        export_format=find_format("png8"),
    )
    assert exported == [str(png_destination)]
    assert png_destination.read_bytes() == Path(image.png_path).read_bytes()

    tif_destination = tmp_path / "copy.tif"
    workspace.export(
        image,
        str(tif_destination),
        exported.append,
        lambda message: pytest.fail(message),
        export_format=find_format("tiff16-lzw"),
    )
    assert engine.calls[-1][0] == "image-0001-export"
    assert engine.calls[-1][1][1] == image.tiff_path
    assert "-compress" in engine.calls[-1][1]
    assert "LZW" in engine.calls[-1][1]
    assert exported[-1] == str(tif_destination)


def test_failed_import_stops_before_preview(tmp_path, monkeypatch):
    engine = FakeEngine(fail_on="-import")
    workspace = _workspace(tmp_path, monkeypatch, engine)
    source = tmp_path / "source.png"
    source.write_bytes(b"source")
    errors = []

    workspace.prepare(str(source), lambda *_: pytest.fail("should not be ready"), errors.append)

    assert len(engine.calls) == 1
    assert errors and "TIFF import failed" in errors[0]


def test_undo_redo_are_isolated_per_image(tmp_path, monkeypatch):
    engine = FakeEngine()
    workspace = _workspace(tmp_path, monkeypatch, engine)
    source = tmp_path / "source.png"
    source.write_bytes(b"source")
    first = workspace.prepare(str(source), lambda *_: None, lambda message: pytest.fail(message))
    second = workspace.prepare(str(source), lambda *_: None, lambda message: pytest.fail(message))
    before_first = Path(first.tiff_path).read_bytes()
    before_second = Path(second.tiff_path).read_bytes()

    workspace.transform(first, {"resize": "50%"}, lambda *_: None, lambda message: pytest.fail(message))
    workspace.transform(second, {"blur": "0x2"}, lambda *_: None, lambda message: pytest.fail(message))
    assert workspace.can_undo(first) and workspace.can_undo(second)

    workspace.undo(first, lambda *_: None, lambda message: pytest.fail(message))
    assert Path(first.tiff_path).read_bytes() == before_first
    assert Path(second.tiff_path).read_bytes() != before_second
    assert workspace.can_undo(second)


def test_skystacker_filter_receives_working_tiff_directly(tmp_path, monkeypatch):
    from astrostudio.adapters import SkyStackerAdapter

    calls = []
    product = tmp_path / "working_blur.jpg"
    product.write_bytes(b"product")

    def fake_run(job_id, argv, on_log=None, on_done=None):
        calls.append((job_id, list(argv)))
        if job_id.endswith("-sky-tiff"):
            Path(_output_path(argv)).write_bytes(b"tiff")
        if "-preview-" in job_id:
            Path(_output_path(argv)).write_bytes(b"png")
        if on_done is not None:
            on_done(JobResult(job_id=job_id, argv=list(argv), exit_code=0))

    class LocalEngine:
        def run(self, job_id, argv, on_log=None, on_done=None):
            fake_run(job_id, argv, on_log, on_done)

    monkeypatch.setattr(
        SkyStackerAdapter, "find_image_product", lambda *args: str(product)
    )
    workspace = _workspace(tmp_path, monkeypatch, FakeEngine())
    source = tmp_path / "source.png"
    source.write_bytes(b"source")
    image = workspace.prepare(str(source), lambda *_: None, lambda message: pytest.fail(message))
    workspace.engine = LocalEngine()
    ready = []

    workspace.transform_via_image_op(
        image,
        SkyStackerAdapter(),
        "blur",
        ["--denoise-radius", "4"],
        ready.append,
        lambda message: pytest.fail(message),
    )
    sky_call = [call for call in calls if call[0].endswith("-sky-blur")][0]
    assert sky_call[1][2] == image.tiff_path
    assert "--image-op" in sky_call[1]
    assert ready == [image]


def test_unusual_fits_is_rejected_before_cli(tmp_path, monkeypatch):
    from astrostudio.core.fits_hdus import inspect_fits

    engine = FakeEngine()
    workspace = _workspace(tmp_path, monkeypatch, engine)
    primary = header_bytes([
        "SIMPLE  =                    T", "BITPIX  =                   16",
        "NAXIS   =                    2", "NAXIS1  =                    4",
        "NAXIS2  =                    4", "END",
    ])
    extension = header_bytes([
        "XTENSION= 'IMAGE   '", "BITPIX  =                   16",
        "NAXIS   =                    2", "NAXIS1  =                    4",
        "NAXIS2  =                    4", "END",
    ])
    source = tmp_path / "multi.fits"
    source.write_bytes(primary + b"\0" * 2880 + extension + b"\0" * 2880)
    assert inspect_fits(str(source))["unusual"]

    errors = []
    workspace.prepare(str(source), lambda *_: None, errors.append)
    assert errors and "single image HDU" in errors[0]
    assert engine.calls == []


def test_hardlink_snapshots_respect_history_depth(tmp_path, monkeypatch):
    import os

    engine = FakeEngine()
    workspace = _workspace(tmp_path, monkeypatch, engine, history_depth=2)
    source = tmp_path / "source.png"
    source.write_bytes(b"source")
    image = workspace.prepare(str(source), lambda *_: None, lambda message: pytest.fail(message))
    original = Path(image.tiff_path).read_bytes()
    linked = workspace._snapshot(image, workspace._undo)
    assert os.stat(linked.tiff_path).st_nlink >= 2

    for _ in range(3):
        workspace.transform(
            image, {"resize": "50%"}, lambda *_: None,
            lambda message: pytest.fail(message),
        )

    stack = workspace._undo[image.key]
    assert len(stack) == 2
    assert not os.path.exists(os.path.join(image.directory, "snapshot_001.tiff"))

    workspace.undo(image, lambda *_: None, lambda message: pytest.fail(message))
    assert Path(image.tiff_path).read_bytes() != original
    assert os.stat(image.tiff_path).st_nlink >= 2


def test_prepare_flags_8bit_source(tmp_path, monkeypatch):
    workspace = _workspace(tmp_path, monkeypatch, FakeEngine())
    source = tmp_path / "source.png"
    header = bytearray(26)
    header[:8] = b"\x89PNG\r\n\x1a\n"
    header[24] = 8
    source.write_bytes(bytes(header))
    logs = []
    image = workspace.prepare(str(source), lambda *_: None, lambda m: pytest.fail(m), on_log=logs.append)
    assert image.source_depth == 8
    assert any("8-bit source promoted" in line for line in logs)


def test_prepare_flags_float_fits_and_scaling(tmp_path, monkeypatch):
    workspace = _workspace(tmp_path, monkeypatch, FakeEngine())
    cards = [
        "SIMPLE  =                    T / ok",
        "BITPIX  =                  -32 / float",
        "NAXIS   =                    2",
        "NAXIS1  =                    4",
        "NAXIS2  =                    4",
        "BZERO   =                  0.0",
        "BSCALE  =                  1.0",
    ]
    source = tmp_path / "float.fits"
    source.write_bytes(header_bytes(cards + ["END"]) + b"\0" * 2880)
    logs = []
    image = workspace.prepare(str(source), lambda *_: None, lambda m: pytest.fail(m), on_log=logs.append)
    assert image.float_source is True
    assert image.scaling == {"BZERO": 0.0, "BSCALE": 1.0}
    assert any("FITS float source" in line for line in logs)
    assert any("FITS scaling keywords" in line for line in logs)


def test_stale_preview_callback_is_discarded(tmp_path, monkeypatch):
    workspace = _workspace(tmp_path, monkeypatch, FakeEngine())
    source = tmp_path / "source.png"
    source.write_bytes(b"source")
    image = workspace.prepare(str(source), lambda *_: None, lambda m: pytest.fail(m))
    pending = []

    class DeferredEngine:
        def run(self, job_id, argv, on_log=None, on_done=None):
            Path(_output_path(argv)).write_bytes(job_id.encode())
            pending.append(
                (job_id, on_done, JobResult(job_id=job_id, argv=list(argv), exit_code=0))
            )

    workspace.engine = DeferredEngine()
    ready = []
    workspace.update_preview(image, ready.append, lambda m: pytest.fail(m))
    workspace.update_preview(image, ready.append, lambda m: pytest.fail(m))
    assert len(pending) == 2
    pending[0][1](pending[0][2])
    assert ready == []
    pending[1][1](pending[1][2])
    assert len(ready) == 1


def test_failed_transform_keeps_undo_history_empty(tmp_path, monkeypatch):
    workspace = _workspace(tmp_path, monkeypatch, FakeEngine(fail_on="-transform"))
    source = tmp_path / "source.png"
    source.write_bytes(b"source")
    image = workspace.prepare(str(source), lambda *_: None, lambda m: pytest.fail(m))
    workspace.transform(
        image, {"resize": "50%"}, lambda *_: None, lambda message: None
    )
    assert not workspace.can_undo(image)
    assert not workspace.can_redo(image)


def test_prepare_can_force_display_stretch(tmp_path, monkeypatch):
    engine = FakeEngine()
    workspace = _workspace(tmp_path, monkeypatch, engine)
    source = tmp_path / "sky_map.png"
    source.write_bytes(b"png")
    image = workspace.prepare(
        str(source), lambda *_: None, lambda m: pytest.fail(m), display_stretch=True
    )
    assert image.display_stretch is True
