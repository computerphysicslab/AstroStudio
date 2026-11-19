"""Menu structure and resize action tests."""

from astrostudio.app import iter_menu_actions
from astrostudio.ui.main_window import (
    IMAGE_EXTENSIONS,
    MENU_LAYOUT,
    log_segments,
    toggle_label,
)


def test_resize_actions_are_registered():
    actions = set(iter_menu_actions())
    assert {
        "resize-10",
        "resize-25",
        "resize-50",
        "resize-75",
        "resize-100",
        "resize-150",
        "resize-200",
        "resize-400",
        "resize-1000",
        "resize-custom",
    } <= actions
    assert "zoom-1-1" not in actions


def test_log_segments_colourise_commands_and_errors():
    segments = log_segments("[12:00:00] CLI j1: convert -blur 0x2 in.tiff out.tiff")
    assert segments[0][1] == "timestamp"
    assert segments[1][1] == "command_label"
    assert any(text.strip() == "-blur" and tag == "argument" for text, tag in segments)
    assert any(text.strip() == "convert" and tag == "program" for text, tag in segments)
    assert log_segments("[12:00:01] [stderr] boom")[1][1] == "error"


def test_toggle_label_reflects_panel_state():
    assert toggle_label("toggle-backends", "Backends Viewer", True) == "Backends Viewer: On"
    assert toggle_label("toggle-backends", "Backends Viewer", False) == "Backends Viewer: Off"


def test_dock_toggle_is_available_and_cancel_is_gone():
    actions = set(iter_menu_actions())
    assert "toggle-backends" in actions
    assert "toggle-terminal" in actions
    assert "cancel" not in actions


def test_filter_submenus_expose_more_than_ten_actions():
    filter_menu = dict(MENU_LAYOUT)["Filter"]
    actions = set(iter_menu_actions())
    expected = {
        "unsharp",
        "filter-sharpen",
        "filter-convolve-sharpen",
        "filter-blur",
        "filter-gaussian-blur",
        "filter-median",
        "filter-despeckle",
        "filter-adaptive-blur",
        "filter-convolve-gaussian",
        "filter-morphology-erode",
        "filter-edge",
        "filter-emboss",
        "filter-star-reduction",
    }
    assert expected <= actions
    assert all(len(item) == 3 for item in filter_menu)


def test_open_filter_covers_astronomical_formats():
    assert {"png", "jpg", "jpeg", "tif", "tiff", "fits", "bmp", "cr2"} <= set(
        IMAGE_EXTENSIONS
    )


def test_about_is_registered_and_processing_has_no_duplicate_sharpen():
    actions = set(iter_menu_actions())
    assert "about" in actions
    processing = dict(MENU_LAYOUT)["Processing"]
    assert all(item[0] != "Sharpen..." for item in processing)


def test_astrometry_menu_is_registered():
    actions = set(iter_menu_actions())
    assert {"plate-solve", "sky-map", "survey-cutout"} <= actions
    assert "Astrometry" in dict(MENU_LAYOUT)


def test_processing_resize_submenu_has_scales_and_custom():
    processing = dict(MENU_LAYOUT)["Processing"]
    submenu = next(item for item in processing if item[0] == "Resize Image")
    assert submenu[1] is None
    labels = [label for label, _action in submenu[2] if label]
    assert "10%" in labels and "1000%" in labels
    assert "Custom Scale..." in labels
    assert "Fit to Window" not in labels
    assert "1:1 (pixel per pixel)" not in labels
    actions = set(iter_menu_actions())
    assert {"unsharp", "export"} <= actions
    assert "resize" not in actions
