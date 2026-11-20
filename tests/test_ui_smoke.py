"""GUI smoke tests: menus, dock toggles and metadata/histogram panels."""

import pytest

from astrostudio.app import ACTION_NAMES, AstroStudioApplication
from astrostudio.ui import MainWindow


@pytest.fixture
def window():
    app = AstroStudioApplication()
    win = MainWindow(app, app.registry, app.scratch, app.engine)
    yield win
    win.destroy()


def test_window_starts_with_layers_and_actions(window):
    assert window.get_title() == "Astro Studio"
    assert "toggle-star-layer" in ACTION_NAMES
    assert "toggle-object-layer" in ACTION_NAMES
    labels = [label for label, _entries in window.menus.layout]
    assert "View" in labels and "Layers" in [
        item[0] for item in dict(window.menus.layout)["View"] if item[0]
    ]
    model = window._build_menu_model()
    assert model.get_n_items() >= 6


def test_dock_toggles_change_visibility(window):
    for action in (
        "toggle-backends",
        "toggle-resources",
        "toggle-histogram",
        "toggle-terminal",
        "toggle-jobs",
    ):
        panel = window.docks.panel_for_action(action)
        before = panel.get_visible()
        window.docks.toggle(action)
        assert panel.get_visible() is not before
        window.docks.toggle(action)
        assert panel.get_visible() is before


def test_metadata_and_histogram_panels_exist(window):
    assert window.metadata_panel is not None
    assert window.metadata_panel.get_no_show_all()
    assert window.histogram_panel is not None
    assert window.docks.panel_for_action("toggle-histogram") is window.histogram_panel
    assert window.histogram_widget is not None
