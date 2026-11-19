"""Startup and geometry regressions for MainWindow."""

import os

import pytest

from gi.repository import Gtk

from astrostudio.app import AstroStudioApplication
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
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    assert window.job_panel is not None
    assert window.backends_panel is not None
    assert window.histogram_panel is not None
    window.show_all()
    minimum, _natural = window.get_preferred_size()
    assert isinstance(window.right_scroll, Gtk.ScrolledWindow)
    assert minimum.height < 400
    assert geometry_warning(minimum.height, 768) is None
    window.validate_geometry()
    window.destroy()
