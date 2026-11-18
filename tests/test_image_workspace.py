"""Dual-format TIFF/PNG workspace tests."""

import os
from pathlib import Path

import pytest

from astrostudio.adapters import ImageMagickAdapter
from astrostudio.core import ImageWorkspace, ScratchManager
from astrostudio.core.export_formats import find_format
from astrostudio.core.process_engine import JobResult


class FakeEngine:
    def __init__(self, fail_on=None):
        self.calls = []
        self.fail_on = fail_on

    def run(self, job_id, argv, on_log=None, on_done=None):
        self.calls.append((job_id, list(argv)))
        if self.fail_on and job_id.endswith(self.fail_on):
            on_done(JobResult(job_id=job_id, argv=list(argv), exit_code=1, stderr="boom"))
            return
        Path(argv[-1]).write_bytes(("data:" + job_id).encode())
        on_done(JobResult(job_id=job_id, argv=list(argv), exit_code=0))


def _workspace(tmp_path, monkeypatch, engine):
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    (tmp_path / "runtime").mkdir()
    return ImageWorkspace(
        ScratchManager("session"), engine, ImageMagickAdapter(binary="convert")
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
    assert engine.calls[1][0] == "image-0001-preview"
    assert "-depth" in engine.calls[1][1] and "8" in engine.calls[1][1]
    assert ready == [image]
    assert Path(image.tiff_path).read_bytes() == b"data:image-0001-import"
    assert Path(image.png_path).read_bytes() == b"data:image-0001-preview"
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
    assert engine.calls[-2][1][-2] == image.tiff_path
    assert engine.calls[-2][1][-1].endswith("working_next.tiff")
    assert "-resize" in engine.calls[-2][1]
    assert "50%" in engine.calls[-2][1]
    assert engine.calls[-1][0] == "image-0001-preview"
    assert ready == [image]
    assert Path(image.tiff_path).read_bytes() == b"data:image-0001-transform"
    assert Path(image.png_path).read_bytes() == b"data:image-0001-preview"
    assert not os.path.exists(os.path.join(image.directory, "working_next.tiff"))


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
    assert Path(image.png_path).read_bytes() == b"data:image-0001-preview"


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
