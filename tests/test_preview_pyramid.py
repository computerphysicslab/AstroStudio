"""Preview pyramid tests."""

import gi

gi.require_version("GdkPixbuf", "2.0")

import pytest
from gi.repository import GdkPixbuf

from astrostudio.core.preview_pyramid import choose_level
from astrostudio.ui.preview import PreviewPane


def test_choose_level_prefers_finest_suitable_level():
    levels = [("/tmp/p25.png", 0.25), ("/tmp/p50.png", 0.5)]
    assert choose_level(levels, 0.1) == levels[0]
    assert choose_level(levels, 0.4) == levels[1]
    assert choose_level([], 1.0) is None


def test_workspace_generates_pyramid_levels(tmp_path, monkeypatch):
    from astrostudio.adapters import ImageMagickAdapter
    from astrostudio.core import ImageWorkspace, ScratchManager
    from test_image_workspace import FakeEngine, _workspace

    engine = FakeEngine()
    workspace = _workspace(tmp_path, monkeypatch, engine)
    source = tmp_path / "source.png"
    source.write_bytes(b"source")
    image = workspace.prepare(str(source), lambda *_: None, lambda m: pytest.fail(m))
    ready = []
    workspace.ensure_pyramid(image, ready.append, lambda m: pytest.fail(m))
    assert [call[0] for call in engine.calls[-2:]] == [
        "image-0001-pyramid-0", "image-0001-pyramid-1"
    ]
    assert len(ready[0]) == 2


def test_preview_switches_pyramid_level_by_zoom(tmp_path):
    paths = []
    for name, size in (("preview_25.png", 4), ("preview_50.png", 8)):
        path = tmp_path / name
        pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, size, size)
        pixbuf.savev(str(path), "png", [], [])
        paths.append((str(path), size / 16.0))

    pane = PreviewPane()
    pane.fit = False
    pane.zoom = 0.1
    pane.set_pyramid(paths, (16, 16))
    assert pane.path.endswith("preview_25.png")
    assert pane.logical_size == (16, 16)

    pane.zoom = 1.0
    pane._refresh_level()
    assert pane.path.endswith("preview_50.png")
