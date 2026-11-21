"""Preview pyramid and fit-to-window regression tests."""

import shutil
import subprocess
from types import SimpleNamespace

import cairo
import gi

gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")

import pytest
from gi.repository import Gdk, GdkPixbuf, GLib

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


def _wait_until(predicate, seconds=20):
    loop = GLib.MainLoop()

    def check():
        if predicate():
            loop.quit()
            return False
        return True

    GLib.timeout_add(50, check)
    GLib.timeout_add(seconds * 1000, loop.quit)
    loop.run()


def _pulse():
    loop = GLib.MainLoop()
    GLib.timeout_add(50, lambda: loop.quit() or False)
    loop.run()


def _solid_png(path, width, height, colour=0xFF0000FF):
    pixbuf = GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, width, height)
    pixbuf.fill(colour)
    pixbuf.savev(str(path), "png", [], [])


def _pyramid_files(tmp_path, width=800, height=600):
    full = tmp_path / "full.png"
    _solid_png(full, width, height)
    levels = []
    for scale in (0.25, 0.5):
        path = tmp_path / ("preview_%d.png" % int(scale * 100))
        _solid_png(path, int(width * scale), int(height * scale))
        levels.append((str(path), scale))
    return full, levels


@pytest.mark.skipif(shutil.which("convert") is None, reason="ImageMagick required")
def test_pyramid_levels_are_actually_downscaled(tmp_path):
    from PIL import Image

    from astrostudio.adapters import ImageMagickAdapter

    adapter = ImageMagickAdapter()
    source = tmp_path / "source.png"
    Image.new("RGB", (400, 300), "blue").save(str(source))
    tiff = tmp_path / "working.tiff"
    subprocess.run(adapter.build_import_argv(str(source), str(tiff)), check=True)
    for scale, size in ((0.25, (100, 75)), (0.5, (200, 150))):
        output = tmp_path / ("level_%d.png" % int(scale * 100))
        subprocess.run(
            adapter.build_pyramid_argv(str(tiff), str(output), scale), check=True
        )
        with Image.open(str(output)) as image:
            assert image.format == "PNG"
            assert image.size == size


@pytest.mark.skipif(shutil.which("convert") is None, reason="ImageMagick required")
def test_workspace_pyramid_files_match_declared_scales(tmp_path, monkeypatch):
    from PIL import Image

    from astrostudio.adapters import ImageMagickAdapter
    from astrostudio.core import ImageWorkspace, ProcessEngine, ScratchManager

    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    (tmp_path / "runtime").mkdir()
    source = tmp_path / "source.png"
    Image.new("RGB", (400, 300), "green").save(str(source))
    workspace = ImageWorkspace(
        ScratchManager("diag"), ProcessEngine(), ImageMagickAdapter()
    )
    opened = []
    workspace.prepare(str(source), opened.append, lambda m: pytest.fail(m))
    _wait_until(lambda: bool(opened))
    image = opened[0]
    levels = []
    workspace.ensure_pyramid(image, levels.append, lambda m: pytest.fail(m))
    _wait_until(lambda: bool(levels))
    assert len(levels) == 1
    for path, scale in levels[0]:
        with Image.open(path) as level_image:
            assert level_image.size == (int(400 * scale), int(300 * scale))


def test_workspace_reports_no_levels_when_adapter_cannot_downscale(tmp_path, monkeypatch):
    from astrostudio.adapters import ImageMagickAdapter
    from astrostudio.core import ImageWorkspace, ScratchManager
    from test_image_workspace import FakeEngine

    class NoPyramidAdapter(ImageMagickAdapter):
        build_pyramid_argv = None

    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    (tmp_path / "runtime").mkdir()
    engine = FakeEngine()
    workspace = ImageWorkspace(
        ScratchManager("diag"), engine, NoPyramidAdapter(binary="convert")
    )
    source = tmp_path / "source.png"
    source.write_bytes(b"source")
    opened = []
    workspace.prepare(str(source), opened.append, lambda m: pytest.fail(m))
    ready = []
    workspace.ensure_pyramid(opened[0], ready.append, lambda m: pytest.fail(m))
    assert ready == [[]]
    assert not any("pyramid" in call[0] for call in engine.calls)


def test_pane_ignores_full_size_level(tmp_path):
    full, levels = _pyramid_files(tmp_path, 100, 80)
    mislabelled = tmp_path / "mislabelled.png"
    shutil.copyfile(str(full), str(mislabelled))
    pane = PreviewPane()
    pane.load(str(full))
    pane.set_pyramid([(str(mislabelled), 0.25)], (100, 80))
    assert pane.path == str(full)
    assert pane.level_scale == 1.0


def test_fit_with_real_pyramid_level_stays_inside_canvas(tmp_path, monkeypatch):
    full, levels = _pyramid_files(tmp_path)
    pane = PreviewPane()
    allocation = SimpleNamespace(width=500, height=400)
    monkeypatch.setattr(pane, "get_allocation", lambda: allocation)
    pane.load(str(full))
    pane.set_pyramid(levels, (800, 600))

    _, scale, offset_x, offset_y = pane._view_parameters()
    assert abs(scale - 0.625) < 1e-9
    assert offset_x >= -0.01 and offset_y >= -0.01
    assert offset_x + 800 * scale <= 500.01
    assert offset_y + 600 * scale <= 400.01

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 500, 400)
    cr = cairo.Context(surface)
    assert pane._on_draw(pane, cr) is False

    def pixel(x, y):
        data = surface.get_data()
        index = y * surface.get_stride() + x * 4
        return data[index + 2], data[index + 1], data[index]

    assert pixel(250, 200)[0] > 200
    assert pixel(250, 200)[1] < 40
    assert pixel(250, 5)[0] < 40
    assert pixel(250, 395)[0] < 40


def test_double_click_zoom_fit_resets_manual_zoom():
    from astrostudio.app import AstroStudioApplication
    from astrostudio.ui import MainWindow

    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    window.show_all()
    pane = window.preview
    pane.set_pixbuf(GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 800, 600))
    pane.set_zoom_scale(2.0)
    pane.pan_x = 40.0
    pane.pan_y = 25.0
    pane.set_rotation_mode(True)
    event = SimpleNamespace(
        button=1, type=Gdk.EventType.DOUBLE_BUTTON_PRESS, x=10.0, y=10.0
    )
    window._on_canvas_click(pane, event)
    assert pane.fit is True
    assert (pane.pan_x, pane.pan_y) == (0.0, 0.0)
    window.destroy()


def test_allocation_change_refreshes_fit_level(tmp_path, monkeypatch):
    full, levels = _pyramid_files(tmp_path)
    pane = PreviewPane()
    allocation = SimpleNamespace(width=500, height=400)
    monkeypatch.setattr(pane, "get_allocation", lambda: allocation)
    pane.load(str(full))
    pane.set_pyramid(levels, (800, 600))
    assert pane.path.endswith("preview_50.png")

    allocation.width = 800
    allocation.height = 600
    pane._on_size_allocate(pane, allocation)
    _pulse()
    _, scale, offset_x, offset_y = pane._view_parameters()
    assert abs(scale - 1.0) < 1e-9
    assert 800 * scale <= 800.01
    assert 600 * scale <= 600.01
    assert abs(offset_x) < 0.01 and abs(offset_y) < 0.01
