"""Menu structure and precise-scale action tests."""

from astrostudio.app import iter_menu_actions
from astrostudio.ui.main_window import MENU_LAYOUT


def test_precise_scale_actions_are_registered():
    actions = set(iter_menu_actions())
    assert {
        "zoom-10",
        "zoom-25",
        "zoom-50",
        "zoom-75",
        "zoom-100",
        "zoom-150",
        "zoom-200",
        "zoom-400",
        "zoom-1000",
        "zoom-1-1",
        "zoom-fit",
    } <= actions


def test_dock_toggle_is_available_and_cancel_is_gone():
    actions = set(iter_menu_actions())
    assert "toggle-backends" in actions
    assert "cancel" not in actions


def test_processing_contains_precise_scale_submenu_and_cli_actions():
    processing = dict(MENU_LAYOUT)["Processing"]
    submenu = next(item for item in processing if item[0] == "Precise Scale")
    assert submenu[1] is None
    labels = [label for label, _action in submenu[2] if label]
    assert "1:1 (pixel per pixel)" in labels
    assert "Fit to Window" in labels
    actions = set(iter_menu_actions())
    assert {"resize", "unsharp", "export"} <= actions
