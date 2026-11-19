"""Startup regression: MainWindow must build with all dock panels."""

import os

import pytest

from astrostudio.app import AstroStudioApplication
from astrostudio.ui import MainWindow

pytestmark = pytest.mark.skipif(
    not os.environ.get("DISPLAY"), reason="GTK display required"
)


def test_main_window_builds_with_job_panel():
    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    assert window.job_panel is not None
    assert window.backends_panel is not None
    assert window.histogram_panel is not None
    window.destroy()
