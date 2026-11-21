"""UI interaction regressions requiring a GTK display."""

import json
import math
import os
from pathlib import Path

import gi
import pytest

gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gdk, GdkPixbuf, GLib, Gtk

from astrostudio.app import AstroStudioApplication
from astrostudio.core import WorkingImage
from astrostudio.core.process_engine import JobResult
from astrostudio.ui import MainWindow, PreviewPane

pytestmark = pytest.mark.skipif(
    not os.environ.get("DISPLAY"), reason="GTK display required"
)


def _sample_pixbuf():
    return GdkPixbuf.Pixbuf.new(GdkPixbuf.Colorspace.RGB, False, 8, 64, 48)


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
    monkeypatch.setattr(window, "_rotate_image", lambda angle, label, relaunch=None: angles.append(angle))

    window.preview.set_select_mode(True)
    window.action_rotate_segment()
    assert window.preview.rotation_mode
    assert not window.preview.select_mode
    window._rotation_enabled_at = 0.0

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
    rotations = []
    monkeypatch.setattr(
        window,
        "_rotate_image",
        lambda angle, label, relaunch=None: rotations.append((angle, label, relaunch)),
    )
    segment.activate()
    assert window.preview.rotation_mode
    window._rotation_enabled_at = 0.0
    press = Gdk.Event.new(Gdk.EventType.BUTTON_PRESS)
    press.button, press.x, press.y = 1, 100, 100
    window._on_canvas_click(window.preview, press)
    motion = Gdk.Event.new(Gdk.EventType.MOTION_NOTIFY)
    motion.x, motion.y = 180, 100
    window._on_canvas_motion(window.preview, motion)
    release = Gdk.Event.new(Gdk.EventType.BUTTON_RELEASE)
    window._on_canvas_release(window.preview, release)
    assert not window.preview.rotation_mode
    assert rotations == [(0, "Rotate by segment", "rotate-segment")]
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


def test_rotation_survives_release_before_segment(monkeypatch):
    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    angles = []
    monkeypatch.setattr(window, "_rotate_image", lambda angle, label, relaunch=None: angles.append(angle))
    window.action_rotate_segment()
    window._rotation_enabled_at = 0.0
    stray_release = Gdk.Event.new(Gdk.EventType.BUTTON_RELEASE)
    window._on_canvas_release(window.preview, stray_release)
    assert window.preview.rotation_mode
    assert angles == []
    window.preview.start_rotation(10, 10)
    window.preview.update_rotation(60, 10)
    window._on_canvas_release(window.preview, Gdk.Event.new(Gdk.EventType.BUTTON_RELEASE))
    assert angles == [0]
    assert not window.preview.rotation_mode
    window.destroy()


def test_star_layer_draws_all_detections(monkeypatch):
    from types import SimpleNamespace

    import cairo

    from astrostudio.core.star_catalog import StarDetection

    pane = PreviewPane()
    pane.set_pixbuf(_sample_pixbuf(), "sample")
    stars = [StarDetection(20 + i * 15, 20, 100 - i, 4, 0.1, 2) for i in range(12)]
    pane.set_star_layer(stars)
    monkeypatch.setattr(
        pane,
        "_view_parameters",
        lambda: (SimpleNamespace(width=400, height=200), 1.0, 0.0, 0.0),
    )
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 400, 200)
    pane._on_draw(None, cairo.Context(surface))
    data = surface.get_data()
    marked = 0
    for offset in range(0, len(data), 4):
        blue, green, red, alpha = data[offset], data[offset + 1], data[offset + 2], data[offset + 3]
        if red > 180 and green > 120 and blue < 120 and alpha > 0:
            marked += 1
    assert marked > 200


def test_layer_hover_hit_test(monkeypatch):
    from types import SimpleNamespace

    from astrostudio.core.star_catalog import StarDetection

    pane = PreviewPane()
    pane.set_pixbuf(_sample_pixbuf(), "sample")
    pane.set_star_layer([StarDetection(50, 40, 90, 4, 0.2, 3)])
    monkeypatch.setattr(
        pane,
        "_view_parameters",
        lambda: (SimpleNamespace(width=400, height=200), 1.0, 0.0, 0.0),
    )
    text, target = pane._layer_hit(52, 40)
    assert "Star #1" in text and target == ("star", 1)
    text, target = pane._layer_hit(50, 40)
    assert "flux=90.00" in text and target == ("star", 1)
    assert pane._layer_hit(300, 150) == (None, None)


def test_recent_transforms_deduplicated_and_relaunched(monkeypatch):
    app = AstroStudioApplication()
    app.settings.set("recent_transforms", [])
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    for _ in range(2):
        window._record_recent("Rotate by segment", {"rotate": "12"}, "rotate-segment")
    assert len(window.recent_transforms) == 1
    assert window.recent_transforms[0]["relaunch"] == "rotate-segment"

    launched = []
    monkeypatch.setattr(window, "action_rotate_segment", lambda: launched.append(True))
    monkeypatch.setattr(
        window, "_run_transform", lambda *_args, **_kwargs: (_ for _ in ()).throw(
            AssertionError("must not reapply fixed angle")
        )
    )
    window._reapply_transform(window.recent_transforms[0])
    assert launched == [True]
    window.destroy()


def test_context_menu_keeps_open_recent(monkeypatch, tmp_path):
    app = AstroStudioApplication()
    app.settings.set("recent_transforms", [])
    app.settings.set("recent_images", [str(tmp_path / "M42.jpg"), str(tmp_path / "M31.jpg")])
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    monkeypatch.setattr(Gtk.Menu, "popup_at_pointer", lambda self, event: None)
    event = Gdk.Event.new(Gdk.EventType.BUTTON_PRESS)
    window._show_app_menu(event)
    file_item = next(
        item for item in window._app_popup.get_children()
        if item.get_label() == "File"
    )
    labels = [item.get_label() for item in file_item.get_submenu().get_children()]
    assert "Open Recent" in labels
    recent_index = labels.index("Open Recent")
    assert "Open" in labels[:recent_index]
    recent_item = file_item.get_submenu().get_children()[recent_index]
    recent_labels = [item.get_label() for item in recent_item.get_submenu().get_children()]
    assert recent_labels == ["M42.jpg", "M31.jpg"]
    window.destroy()


def test_context_menu_open_recent_fallback(monkeypatch):
    app = AstroStudioApplication()
    app.settings.set("recent_images", [])
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    monkeypatch.setattr(Gtk.Menu, "popup_at_pointer", lambda self, event: None)
    window._show_app_menu(Gdk.Event.new(Gdk.EventType.BUTTON_PRESS))
    file_item = next(
        item for item in window._app_popup.get_children()
        if item.get_label() == "File"
    )
    recent_item = next(
        item for item in file_item.get_submenu().get_children()
        if item.get_label() == "Open Recent"
    )
    labels = [item.get_label() for item in recent_item.get_submenu().get_children()]
    assert labels == ["No recent images"]
    window.destroy()


def test_rotation_cursor_restored_on_realized_window(monkeypatch):
    class FakeWindow:
        def __init__(self):
            self.cursor = None

        def set_cursor(self, cursor):
            self.cursor = cursor

    pane = PreviewPane()
    fake = FakeWindow()
    monkeypatch.setattr(pane, "get_window", lambda: fake)
    pane.set_rotation_mode(True)
    assert fake.cursor is not None
    pane.set_rotation_mode(False)
    assert fake.cursor is not None


def test_layer_visibility_toggles():
    pane = PreviewPane()
    assert pane.star_layer_visible and pane.object_layer_visible
    assert not pane.toggle_star_layer()
    assert pane.star_layer_visible is False
    assert pane.toggle_star_layer()
    assert not pane.toggle_object_layer()
    assert pane.toggle_object_layer()


def test_no_segment_reports_status_and_keeps_mode(monkeypatch):
    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    statuses = []
    monkeypatch.setattr(window, "_status", statuses.append)
    monkeypatch.setattr(
        window, "_rotate_image", lambda *a, **k: pytest.fail("must not rotate")
    )
    window.action_rotate_segment()
    window._rotation_enabled_at = 0.0
    press = Gdk.Event.new(Gdk.EventType.BUTTON_PRESS)
    press.button, press.x, press.y = 1, 100, 100
    window._on_canvas_click(window.preview, press)
    window._on_canvas_release(window.preview, Gdk.Event.new(Gdk.EventType.BUTTON_RELEASE))
    assert window.preview.rotation_mode
    assert any("No segment" in text for text in statuses)
    window.destroy()


def test_rank_label_hover_target(monkeypatch):
    from types import SimpleNamespace

    from astrostudio.core.star_catalog import StarDetection

    pane = PreviewPane()
    pane.set_pixbuf(_sample_pixbuf(), "sample")
    pane.set_star_layer([StarDetection(50, 40, 90, 4, 0.2, 3)])
    monkeypatch.setattr(
        pane,
        "_view_parameters",
        lambda: (SimpleNamespace(width=400, height=200), 1.0, 0.0, 0.0),
    )
    text, target = pane._layer_hit(68, 30)
    assert target == ("star", 1)
    assert "Star #1 rank label" in text

def test_hover_highlight_thickens_star_circle(monkeypatch):
    from types import SimpleNamespace

    import cairo

    from astrostudio.core.star_catalog import StarDetection

    pane = PreviewPane()
    pane.set_pixbuf(_sample_pixbuf(), "sample")
    pane.set_star_layer([StarDetection(60, 60, 2, 4, 0.2, 3)])
    monkeypatch.setattr(
        pane,
        "_view_parameters",
        lambda: (SimpleNamespace(width=200, height=140), 1.0, 0.0, 0.0),
    )

    def count_yellow():
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 200, 140)
        pane._on_draw(None, cairo.Context(surface))
        data = surface.get_data()
        return sum(
            1
            for offset in range(0, len(data), 4)
            if data[offset + 2] > 180 and data[offset + 1] > 120
            and data[offset] < 120 and data[offset + 3] > 0
        )

    normal = count_yellow()
    pane.set_hover_target(("star", 1))
    highlighted = count_yellow()
    assert highlighted > normal


def test_star_labels_do_not_connect_with_lines(monkeypatch):
    from types import SimpleNamespace

    import cairo

    from astrostudio.core.star_catalog import StarDetection

    pane = PreviewPane()
    pane.set_pixbuf(_sample_pixbuf(), "sample")
    monkeypatch.setattr(
        pane,
        "_view_parameters",
        lambda: (SimpleNamespace(width=300, height=200), 1.0, 0.0, 0.0),
    )

    def render(stars):
        pane.set_star_layer(stars)
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 300, 200)
        pane._on_draw(None, cairo.Context(surface))
        data = surface.get_data()
        return sum(
            1
            for y in range(80, 120)
            for x in range(100, 200)
            if data[(y * 300 + x) * 4 + 2] > 240
            and 150 < data[(y * 300 + x) * 4 + 1] < 230
            and data[(y * 300 + x) * 4] < 90
        )

    baseline = render([])
    with_stars = render([
        StarDetection(40, 100, 50, 4, 0.2, 3),
        StarDetection(240, 100, 50, 4, 0.2, 3),
    ])
    assert with_stars <= baseline


def test_plate_solve_filename_hint(monkeypatch):
    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    messages = []
    monkeypatch.setattr(window, "_log", messages.append)
    center = window._filename_hint("Orion-M42-Riofrio-2026-11-09.png")
    assert center is not None
    assert "83." in center and ",-5." in center
    assert any("Catalog hint" in message for message in messages)
    assert window._filename_hint("M42-and-M31.png") is None
    window.destroy()


def test_plate_solve_dumbbell_filename_hint(monkeypatch):
    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    messages = []
    monkeypatch.setattr(window, "_log", messages.append)
    center = window._filename_hint("Dumbell-86x30s-refr150-crop_2.png")
    assert center == "299.901583,22.721028"
    assert any("Catalog hint" in message for message in messages)
    window.destroy()


def test_plate_solve_enriches_metadata_without_modifying_source(monkeypatch, tmp_path):
    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    solution = {
        "WCS": {
            "CRVAL1": math.radians(83.822),
            "CRVAL2": math.radians(-5.391),
            "CRPIX1": 0.0,
            "CRPIX2": 0.0,
            "CD": [[math.radians(-0.01), 0.0], [0.0, math.radians(0.01)]],
        },
        "Method": "header",
    }
    (tmp_path / "plate_solution.json").write_text(
        json.dumps(solution), encoding="utf-8"
    )
    source = str(tmp_path / "M42.png")
    (tmp_path / "M42.png").write_bytes(b"original")
    image = WorkingImage(
        "img", source, str(tmp_path), str(tmp_path / "w.tiff"), str(tmp_path / "p.png")
    )
    window.current_images.append(image)
    window.current_paths.append(source)
    monkeypatch.setattr(window, "_show_info", lambda *args: None)
    logs = []
    monkeypatch.setattr(window, "_log", logs.append)
    window._on_plate_solve_done(
        JobResult("plate-solve", [], 0), str(tmp_path)
    )
    sidecar = tmp_path / "M42.metadata.json"
    assert sidecar.exists()
    data = json.loads(sidecar.read_text(encoding="utf-8"))
    assert abs(data["metadata"]["RA_DEG"] - 83.822) < 0.001
    assert abs(data["metadata"]["DEC_DEG"] + 5.391) < 0.001
    assert "RA_DEG" in data["added"] and "DEC_DEG" in data["added"]
    assert (tmp_path / "M42.png").read_bytes() == b"original"
    assert any("Metadata sidecar" in line for line in logs)
    window.destroy()


def test_plate_solve_failure_is_classified_as_external(monkeypatch):
    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)

    class StubLog:
        def __init__(self):
            self.records = []

        def record(self, event, **kwargs):
            self.records.append((event, kwargs))

    errors = []
    log = StubLog()
    monkeypatch.setattr(
        window, "_show_external_failure", lambda *args: errors.append(args)
    )
    monkeypatch.setattr(window, "operation_log", log)
    detail = (
        "gaia: tile nside=64 [cache hit]\n"
        "plate: seeded Gaia solve failed (plate solve: no consistent transform (0 matched pairs))\n"
        "plate: local astrometry.net unavailable"
    )
    window._on_plate_solve_done(
        JobResult("plate-solve", [], 1, stderr=detail), "/tmp/job"
    )
    assert errors and errors[0][0] == "solver-matching"
    assert errors[0][1] == "Star matching failed"
    assert ("external_failure", {"job_id": "plate-solve", "category": "solver-matching"}) in log.records
    window.destroy()


def test_sky_map_done_strips_titles_before_preview(monkeypatch, tmp_path):
    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    output_dir = tmp_path / "job"
    output_dir.mkdir()
    (output_dir / "map.svg").write_text(
        '<svg><circle cx="1" cy="2" r="3"><title>star</title></circle></svg>',
        encoding="utf-8",
    )
    calls = []

    class FakeEngine:
        def run(self, job_id, argv, on_log=None, on_done=None):
            calls.append((job_id, list(argv)))

    monkeypatch.setattr(window, "engine", FakeEngine())
    window._on_sky_map_done(JobResult("sky-map", [], 0), str(output_dir))
    assert calls and calls[0][0] == "sky-map-preview"
    assert "sky_map_display.svg" in calls[0][1][3]
    assert "<title>" not in (output_dir / "sky_map_display.svg").read_text(
        encoding="utf-8"
    )
    window.destroy()


def test_filter_stretch_action_delegates_to_skystacker(monkeypatch):
    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    calls = []
    monkeypatch.setattr(
        window, "_run_sky_filter", lambda op, flags, label: calls.append((op, flags, label))
    )
    window.action_filter_stretch()
    assert calls == [("stretch", [], "Asinh Stretch")]
    window.destroy()


def test_prefetch_passes_catalog_dir_and_reports_failures(monkeypatch):
    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    monkeypatch.setattr(window.registry, "available", lambda name: True)
    captured = {}

    def fake_plan(
        catalogs, source, output_dir, survey, catalog_dir=None, plate_center=None
    ):
        captured["catalog_dir"] = catalog_dir
        captured["plate_center"] = plate_center
        return [["job", "one"], ["job", "two"]]

    monkeypatch.setattr("astrostudio.ui.main_window.prefetch_plan", fake_plan)

    class FailingEngine:
        def run(self, job_id, argv, on_log=None, on_done=None):
            on_done(
                JobResult(
                    job_id, list(argv), exit_code=1, stderr="hips2fits HTTP 404"
                )
            )

    monkeypatch.setattr(window, "engine", FailingEngine())
    logs = []
    statuses = []
    monkeypatch.setattr(window, "_log", logs.append)
    monkeypatch.setattr(window, "_status", statuses.append)
    window.adapters["SkyStacker"].catalog_dir = "/catalogs"
    window.plate_centers["/orig.png"] = "299.901583,22.721028"
    window.current_paths.append("/orig.png")
    window.action_prefetch_catalogs()
    assert captured["catalog_dir"] == "/catalogs"
    assert captured["plate_center"] == "299.901583,22.721028"
    assert any("HTTP 404" in message for message in logs)
    assert any("2 failure" in text for text in statuses)
    window.destroy()


def test_survey_cutout_hints_about_hips_outage(monkeypatch):
    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    errors = []
    monkeypatch.setattr(
        window, "_show_external_failure", lambda *args: errors.append(args)
    )
    window._on_survey_cutout_done(
        JobResult("survey-cutout", [], 1, stderr="skystacker: hips2fits HTTP 404"),
        "/tmp/job",
    )
    assert errors and errors[0][0] == "hips-service"
    assert "CDS HiPS" in errors[0][2]
    window.destroy()


def test_sky_map_image_inherits_plate_solution(monkeypatch, tmp_path):
    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    output_dir = tmp_path / "job"
    output_dir.mkdir()
    svg = output_dir / "map.svg"
    svg.write_text('<svg><circle cx="1" cy="2" r="3"/></svg>', encoding="utf-8")
    (output_dir / "plate_solution.json").write_text("{}", encoding="utf-8")
    png = tmp_path / "sky_map.png"
    png.write_bytes(b"png")
    monkeypatch.setattr(window, "_open_file", lambda path, **kwargs: None)
    window.plate_centers["/orig.png"] = "299.901583,22.721028"
    window.plate_options["/orig.png"] = {"solver": "auto"}
    window._on_sky_map_preview(
        JobResult("sky-map-preview", [], 0), str(png), str(svg), 5, "/orig.png"
    )
    assert window.plate_solutions[str(png)] == str(
        output_dir / "plate_solution.json"
    )
    assert window.plate_centers[str(png)] == "299.901583,22.721028"
    assert window.plate_options[str(png)] == {"solver": "auto"}
    window.destroy()


def test_sky_map_preview_opens_generated_image_in_canvas(monkeypatch, tmp_path):
    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    png = tmp_path / "sky_map.png"
    png.write_bytes(b"png")
    opened = []
    statuses = []
    monkeypatch.setattr(
        window,
        "_open_file",
        lambda path, display_stretch=False: opened.append((path, display_stretch)),
    )
    monkeypatch.setattr(window, "_status", statuses.append)
    window._on_sky_map_preview(
        JobResult("sky-map-preview", [], 0), str(png), "/tmp/map.svg", 105
    )
    assert opened == [(str(png), True)]
    assert any("105" in text for text in statuses)
    window.destroy()


def test_sky_map_preview_reports_render_failure(monkeypatch, tmp_path):
    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    errors = []
    opened = []
    monkeypatch.setattr(window, "_show_error", lambda *args: errors.append(args))
    monkeypatch.setattr(window, "_open_file", lambda *args, **kwargs: opened.append(args))
    result = JobResult("sky-map-preview", [], 1, stderr="renderer exploded")
    window._on_sky_map_preview(result, str(tmp_path / "x.png"), "/tmp/map.svg", 5)
    assert errors and "renderer exploded" in str(errors[0])
    assert not opened
    window.destroy()


def test_sky_map_without_sources_is_reported(monkeypatch, tmp_path):
    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    output_dir = tmp_path / "job"
    output_dir.mkdir()
    (output_dir / "empty.svg").write_text("<svg></svg>", encoding="utf-8")
    errors = []
    monkeypatch.setattr(window, "_show_error", lambda *args: errors.append(args))
    window._on_sky_map_done(JobResult("sky-map", [], 0), str(output_dir))
    assert errors and "empty sky map" in str(errors[0])
    window.destroy()


def test_sky_map_preview_argv_uses_explicit_png_coder():
    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    argv = window._sky_map_preview_argv("in.svg", "out.png")
    assert argv[1:3] == ["-density", "144"]
    assert argv[-1] == "png:out.png"
    window.destroy()


def test_main_window_log_uses_structured_logger(monkeypatch):
    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    seen = []
    monkeypatch.setattr(window.structured_log, "info", seen.append)
    window._log("hello terminal")
    assert seen == ["hello terminal"]
    window.destroy()


def test_open_large_image_fit_survives_pyramid_and_real_allocation(tmp_path, monkeypatch):
    from PIL import Image

    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    (tmp_path / "runtime").mkdir()
    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    window.show_all()
    while Gtk.events_pending():
        Gtk.main_iteration()

    source = tmp_path / "large.png"
    Image.new("RGB", (1200, 900), "purple").save(str(source))
    opened = []
    window.workspace.prepare(str(source), opened.append, lambda m: pytest.fail(m))

    def wait(predicate, seconds=20):
        loop = GLib.MainLoop()

        def check():
            if predicate():
                loop.quit()
                return False
            return True

        GLib.timeout_add(50, check)
        GLib.timeout_add(seconds * 1000, loop.quit)
        loop.run()

    wait(lambda: bool(opened))
    image = opened[0]
    window.preview.load(image.png_path)
    levels_ready = []
    window.workspace.ensure_pyramid(
        image, levels_ready.append, lambda m: pytest.fail(m)
    )
    wait(lambda: bool(levels_ready))
    with Image.open(str(image.png_path)) as preview_image:
        full_size = preview_image.size
    window.preview.set_pyramid(levels_ready[0], full_size)

    allocation = window.preview.get_allocation()
    assert allocation.width > 1 and allocation.height > 1
    _, scale, offset_x, offset_y = window.preview._view_parameters()
    assert window.preview.fit is True
    assert 1200 * scale <= allocation.width + 1
    assert 900 * scale <= allocation.height + 1
    assert offset_x >= -1 and offset_y >= -1
    window.destroy()


def test_terminal_always_scrolls_to_the_last_line():
    app = AstroStudioApplication()
    window = MainWindow(app, app.registry, app.scratch, app.engine)
    window.show_all()
    for index in range(80):
        window._append_log_line("terminal line %d" % index, "info", {})
    loop = GLib.MainLoop()
    GLib.timeout_add(50, lambda: loop.quit() or False)
    loop.run()
    adjustment = window.log_view.get_vadjustment()
    assert adjustment is not None
    assert adjustment.get_value() >= adjustment.get_upper() - adjustment.get_page_size() - 1
    window.destroy()


def test_stop_action_only_enabled_for_user_jobs():
    app = AstroStudioApplication()
    action = app.lookup_action("cancel")
    assert action is not None
    action.set_enabled(True)
    app.update_action_sensitivity()
    assert not action.get_enabled()

    class Engine:
        active_jobs = ["probe-ImageMagick"]

    app.engine = Engine()
    app.update_action_sensitivity()
    assert not action.get_enabled()

    Engine.active_jobs = ["image-0001-import"]
    app.update_action_sensitivity()
    assert action.get_enabled()
