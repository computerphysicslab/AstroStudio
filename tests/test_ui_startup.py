"""Startup and geometry regressions for MainWindow."""

import os

import pytest

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from astrostudio.app import ACTION_NAMES, AstroStudioApplication
from astrostudio.core import SHADOW_LOUPE_HELP, Translator
from astrostudio.ui import MainWindow
from astrostudio.ui.main_window import geometry_warning

pytestmark = pytest.mark.skipif(
    not os.environ.get("DISPLAY"), reason="GTK display required"
)


def test_geometry_warning_helper():
    assert geometry_warning(258, 768) is None
    assert "minimum height 868" in geometry_warning(868, 768)
    assert geometry_warning(100, 0) is None


def test_main_window_builds_with_small_minimum_size():
    app = AstroStudioApplication()
    app.settings.set("show_thumbnails", False)
    app.settings.set("show_resources", True)
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    assert window.job_panel is not None
    assert window.backends_panel is not None
    assert window.histogram_panel is not None
    assert "fullscreen" in ACTION_NAMES
    assert window.thumbnail_scroll.get_visible() is False
    assert window.resources_panel is not None
    window.show_all()
    minimum, _natural = window.get_preferred_size()
    assert isinstance(window.right_scroll, Gtk.ScrolledWindow)
    assert minimum.height < 400
    assert geometry_warning(minimum.height, 768) is None
    window.validate_geometry()
    file_menu = window.menu_bar.get_children()[0].get_submenu()
    labels = [item.get_label() for item in file_menu.get_children()]
    assert labels[:2] == ["Open", "Open Recent"]
    window.destroy()


def test_histogram_info_button_explains_shadow_loupe_in_ui_language():
    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    button = window.histogram_info
    assert button in window.histogram_header.get_children()
    assert button.get_tooltip_text() == SHADOW_LOUPE_HELP
    app.settings.set("language", "es")
    window._apply_language()
    assert button.get_tooltip_text() == Translator("es").tr(SHADOW_LOUPE_HELP)
    assert button.get_tooltip_text() != SHADOW_LOUPE_HELP
    window.destroy()


def test_backends_and_jobs_are_hidden_by_default():
    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    window.show_all()
    assert window.backends_panel.get_no_show_all()
    assert window.job_panel.get_no_show_all()
    assert not window.backends_panel.get_visible()
    assert not window.job_panel.get_visible()
    window.docks.toggle("toggle-backends")
    window.docks.toggle("toggle-jobs")
    assert window.backends_panel.get_visible()
    assert window.job_panel.get_visible()
    assert app.settings.get("show_backends") is True
    assert app.settings.get("show_jobs") is True
    window.destroy()


def test_undo_redo_buttons_reflect_history(tmp_path):
    app = AstroStudioApplication()
    app.settings.set("show_thumbnails", False)
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    app.window = window
    window.show_all()
    app.update_action_sensitivity()
    assert not window.toolbar_buttons["undo"].get_sensitive()
    assert not window.toolbar_buttons["redo"].get_sensitive()
    from astrostudio.core import WorkingImage

    tiff = tmp_path / "w.tiff"
    png = tmp_path / "p.png"
    image = WorkingImage("img", "source.fits", str(tmp_path), str(tiff), str(png))
    window.current_images.append(image)
    tiff.write_bytes(b"tiff")
    png.write_bytes(b"png")
    window.workspace._snapshot(image, window.workspace._undo)
    window.transform_history.append("resize-down")
    app.update_action_sensitivity()
    assert window.toolbar_buttons["undo"].get_sensitive()
    assert not window.toolbar_buttons["redo"].get_sensitive()
    window.destroy()


def test_resource_meters_are_asymmetric():
    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    cpu = window.resource_monitor.cpu_meter
    ram = window.resource_monitor.ram_meter
    assert cpu.get_hexpand()
    assert not ram.get_hexpand()
    assert ram.show_bar is False
    window.destroy()
