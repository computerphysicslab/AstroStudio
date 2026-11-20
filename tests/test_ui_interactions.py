"""UI interaction regressions requiring a GTK display."""

import os
from pathlib import Path

import gi
import pytest

gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gdk, GdkPixbuf, Gtk

from astrostudio.app import AstroStudioApplication
from astrostudio.core import WorkingImage
from astrostudio.ui import MainWindow, PreviewPane

pytestmark = pytest.mark.skipif(
    not os.environ.get("DISPLAY"), reason="GTK display required"
)


def test_selection_hit_test_and_image_rectangle(monkeypatch, tmp_path):
    pane = PreviewPane()
    pane.selection = (10.0, 10.0, 40.0, 30.0)
    assert pane.selection_at(20, 20)
    assert not pane.selection_at(200, 200)

    png = tmp_path / "p.png"
    GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 100, 80).savev(
        str(png), "png", [], []
    )
    pane.pixbuf = GdkPixbuf.Pixbuf.new_from_file(str(png))
    monkeypatch.setattr(pane, "_view_parameters", lambda: (None, 2.0, 0.0, 0.0))
    assert pane.image_rectangle() == (5, 5, 20, 15)


def test_derivation_tree_dialog_opens(monkeypatch, tmp_path):
    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    tiff = tmp_path / "working.tiff"
    png = tmp_path / "preview.png"
    tiff.write_bytes(b"tiff")
    png.write_bytes(b"png")
    window.current_images.append(
        WorkingImage("img", "source.fits", str(tmp_path), str(tiff), str(png))
    )
    monkeypatch.setattr(Gtk.Dialog, "run", lambda self: Gtk.ResponseType.CLOSE)
    window.action_derivation_tree()
    window.destroy()


def test_context_menu_has_menu_and_crop(monkeypatch, tmp_path):
    app = AstroStudioApplication()
    app.settings.set("recent_transforms", [])
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    monkeypatch.setattr(Gtk.Menu, "popup_at_pointer", lambda self, event: None)
    event = Gdk.Event.new(Gdk.EventType.BUTTON_PRESS)
    event.button, event.x, event.y = 3, 50, 50
    window.preview.selection = (10.0, 10.0, 80.0, 60.0)
    window.current_images.append(
        WorkingImage("img", "source.fits", str(tmp_path), str(tmp_path / "w.tiff"), str(tmp_path / "p.png"))
    )
    window._show_context_menu(event)
    items = window._context_popup.get_children()
    assert [item.get_label() for item in items[:2]] == ["menu", "Crop Selection"]
    assert items[1].get_sensitive()
    window.preview.selection = None
    window._show_context_menu(event)
    items = window._context_popup.get_children()
    assert not items[1].get_sensitive()
    window.destroy()


def test_rotation_segment_angle():
    pane = PreviewPane()
    assert pane.segment_angle() is None
    pane.start_rotation(10, 10)
    pane.update_rotation(110, 10)
    assert pane.segment_angle() == 0
    pane.update_rotation(10, 110)
    assert pane.segment_angle() == 90
    assert pane.finish_rotation() == 90
    assert pane.rotation_start is None


def test_rotate_segment_is_exclusive_and_resets(monkeypatch):
    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    angles = []
    monkeypatch.setattr(window, "_rotate_image", lambda angle, label: angles.append(angle))

    window.preview.set_select_mode(True)
    window.action_rotate_segment()
    assert window.preview.rotation_mode
    assert not window.preview.select_mode

    window.preview.start_rotation(10, 10)
    window.preview.update_rotation(60, 10)
    event = Gdk.Event.new(Gdk.EventType.BUTTON_RELEASE)
    window._on_canvas_release(window.preview, event)
    assert angles == [0]
    assert not window.preview.rotation_mode

    window.action_rotate_segment()
    assert window.preview.rotation_mode
    assert not window.preview.select_mode
    window.destroy()


def test_before_after_loads_image_into_canvas(monkeypatch, tmp_path):
    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    opened = []
    monkeypatch.setattr(window, "_open_file", opened.append)
    output = str(tmp_path / "before_after.png")
    result = type("Result", (), {"ok": True})()
    window._on_before_after_done(result, output)
    assert opened == [output]
    window.destroy()


def test_close_shows_previous_image(monkeypatch, tmp_path):
    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    for index in (1, 2):
        png = tmp_path / ("p%d.png" % index)
        GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, True, 8, 8, 8).savev(
            str(png), "png", [], []
        )
        window.current_paths.append(str(png))
        image = WorkingImage(
            "img%d" % index, str(png), str(tmp_path), str(tmp_path / "w.tiff"), str(png)
        )
        window.current_images.append(image)
    window.action_close()
    assert len(window.current_images) == 1
    assert window.preview.path == str(tmp_path / "p1.png")
    window.destroy()


def test_app_popup_menu_triggers_rotate_segment(monkeypatch):
    app = AstroStudioApplication()
    app.window = MainWindow(app, app.registry, app.scratch, app.engine)
    window = app.window
    monkeypatch.setattr(Gtk.Menu, "popup_at_pointer", lambda self, event: None)
    event = Gdk.Event.new(Gdk.EventType.BUTTON_PRESS)
    window._show_app_menu(event)
    processing = next(
        item for item in window._app_popup.get_children()
        if item.get_label() == "Processing"
    )
    rotate_menu = processing.get_submenu()
    rotate_item = next(
        item for item in rotate_menu.get_children()
        if item.get_label() == "Rotate Image"
    )
    segment = next(
        item for item in rotate_item.get_submenu().get_children()
        if item.get_label() == "Rotate by segment..."
    )
    segment.activate()
    assert window.preview.rotation_mode
    window.destroy()


def test_context_menu_shows_recent_transforms(monkeypatch, tmp_path):
    app = AstroStudioApplication()
    app.settings.set("recent_transforms", [{"label": "Sharpen", "params": {"unsharp": "1.5"}}])
    app.window = MainWindow(app, app.registry, app.scratch, app.engine)
    window = app.window
    monkeypatch.setattr(Gtk.Menu, "popup_at_pointer", lambda self, event: None)
    event = Gdk.Event.new(Gdk.EventType.BUTTON_PRESS)
    window._show_context_menu(event)
    labels = [item.get_label() for item in window._context_popup.get_children()]
    assert "Repeat: Sharpen" in labels
    window.destroy()


def test_redo_accelerator_includes_ctrl_y(monkeypatch):
    app = AstroStudioApplication()
    original_get = app.settings.get

    def custom_get(key, default=None):
        return {"redo": "<Control><Shift>z"} if key == "shortcuts" else original_get(key, default)

    monkeypatch.setattr(app.settings, "get", custom_get)
    app.apply_shortcuts()
    assert any("y" in accel for accel in app.get_accels_for_action("app.redo"))
