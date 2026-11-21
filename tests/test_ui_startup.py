"""Startup and geometry regressions for MainWindow."""

import os

import pytest

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from astrostudio.app import ACTION_NAMES, AstroStudioApplication
from astrostudio.core import SHADOW_LOUPE_HELP, Translator
from astrostudio.ui import MainWindow
from astrostudio.ui.main_window import TOOL_ITEMS, geometry_warning

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
    assert window.thumbnail_panel.get_visible() is False
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


def test_toolbar_and_thumbnails_are_dock_panels():
    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    top, bottom = window.right_dock.get_children()
    assert top.get_children()[0] is window.toolbar_panel
    assert top.get_children()[1] is window.resources_panel
    assert bottom is window.terminal_box
    terminal_children = window.terminal_box.get_children()
    assert window.thumbnail_panel in terminal_children
    assert terminal_children[-1] is window.progress_bar
    assert len(window.toolbar_rows) == 2
    assert all(row.get_icon_size() == Gtk.IconSize.MENU for row in window.toolbar_rows)
    fit = window.toolbar_buttons["zoom-fit"]
    assert fit.get_icon_widget().get_property("icon-size") == Gtk.IconSize.MENU
    window.destroy()


def test_compact_widget_details():
    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    titlebar = window.get_titlebar()
    assert titlebar is not None
    assert len(titlebar.get_children()[0].get_children()) == 3
    assert window.preview_frame.get_label_widget() is None
    assert window.thumbnail_view.get_text_column() == -1
    assert window.resource_monitor.cpu_meter.get_size_request()[1] <= 44
    assert window.progress_bar in window.terminal_box.get_children()
    window.destroy()


def test_arabic_language_is_rtl_and_translated():
    app = AstroStudioApplication()
    app.settings.set("language", "ar")
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    assert window.get_direction() == Gtk.TextDirection.RTL
    assert window.translator.tr("Open") == "فتح"
    app.settings.set("language", "en")
    window._apply_language()
    assert window.get_direction() == Gtk.TextDirection.LTR
    window.destroy()


def test_toolbar_groups_and_stop_is_last():
    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    rows = window.toolbar_rows
    separators = [
        item
        for row in rows
        for item in row.get_children()
        if isinstance(item, Gtk.SeparatorToolItem)
    ]
    assert len(separators) == 2
    assert rows[-1].get_children()[-1] is window.toolbar_buttons["cancel"]
    assert "stop-action" in window.toolbar_buttons["cancel"].get_style_context().list_classes()
    assert TOOL_ITEMS[-1][2] == "cancel"
    window.destroy()


def test_right_dock_split_is_resizable_and_persisted():
    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    assert isinstance(window.right_dock, Gtk.Paned)
    assert window.right_dock.get_position() == app.settings.get("right_dock_split")
    window.right_dock.set_position(250)
    assert app.settings.get("right_dock_split") == 250
    window.destroy()


def test_zoom_mode_actions_are_available():
    for action in ("zoom-fill", "zoom-width", "zoom-height"):
        assert action in ACTION_NAMES
    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    for method in ("action_zoom_fill", "action_zoom_width", "action_zoom_height"):
        assert callable(getattr(window, method))
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
