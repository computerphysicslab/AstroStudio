"""Real-CLI integration tests (skipped when ImageMagick is absent)."""

import shutil
import subprocess
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from astrostudio.adapters import ImageMagickAdapter
from astrostudio.core.export_formats import find_format

pytestmark = pytest.mark.skipif(
    shutil.which("convert") is None, reason="ImageMagick 6 convert not installed"
)


def test_fits_export_round_trip_preserves_colour(tmp_path):
    adapter = ImageMagickAdapter(binary="convert")
    source = tmp_path / "colour.png"
    rgb = np.zeros((64, 64, 3), dtype="uint8")
    rgb[:, :, 0] = 200
    rgb[:, :, 1] = 80
    rgb[:, :, 2] = 30
    Image.fromarray(rgb, "RGB").save(str(source))

    tiff = tmp_path / "working.tiff"
    fits = tmp_path / "result.fits"
    restored = tmp_path / "restored.tiff"

    subprocess.run(adapter.build_import_argv(str(source), str(tiff)), check=True)
    subprocess.run(
        list(adapter.build_export_argv(str(tiff), str(fits), find_format("fits16"))),
        check=True,
    )
    subprocess.run(adapter.build_import_argv(str(fits), str(restored)), check=True)

    with Image.open(str(restored)) as image:
        assert image.mode == "RGB"
        pixel = image.getpixel((32, 32))
        assert pixel[0] > pixel[1] > pixel[2]


def test_psd_round_trip_keeps_visible_colour(tmp_path):
    adapter = ImageMagickAdapter(binary="convert")
    source = tmp_path / "colour.png"
    rgb = np.zeros((48, 48, 3), dtype="uint8")
    rgb[:, :, 0] = 220
    rgb[:, :, 1] = 90
    rgb[:, :, 2] = 40
    Image.fromarray(rgb, "RGB").save(str(source))

    tiff = tmp_path / "working.tiff"
    psd = tmp_path / "result.psd"
    restored = tmp_path / "restored.tiff"
    subprocess.run(adapter.build_import_argv(str(source), str(tiff)), check=True)
    subprocess.run(
        list(adapter.build_export_argv(str(tiff), str(psd), find_format("psd8"))),
        check=True,
    )
    subprocess.run(adapter.build_import_argv(str(psd), str(restored)), check=True)

    with Image.open(str(restored)) as image:
        assert image.mode == "RGB"
        pixel = image.getpixel((24, 24))
        assert pixel[0] > pixel[1] > pixel[2]
        assert sum(pixel) > 60


def test_preview_stretch_flag_is_serialised():
    adapter = ImageMagickAdapter(binary="convert")
    argv = list(adapter.build_preview_argv("in.tiff", "out.png", display_stretch=True))
    assert argv == [
        "convert",
        "in.tiff",
        "-evaluate",
        "Pow",
        "0.45",
        "-depth",
        "8",
        "out.png",
    ]


def test_arbitrary_rotation_writes_tiff_with_repage(tmp_path):
    adapter = ImageMagickAdapter(binary="convert")
    source = tmp_path / "wide.png"
    Image.fromarray(
        np.full((60, 100, 3), 120, dtype="uint8"), "RGB"
    ).save(str(source))
    tiff = tmp_path / "working.tiff"
    rotated = tmp_path / "rotated.tiff"
    subprocess.run(adapter.build_import_argv(str(source), str(tiff)), check=True)

    argv = adapter.build_argv([str(tiff)], str(rotated), {"rotate": "55.7496"})
    assert "+repage" in argv
    subprocess.run(argv, check=True)
    with Image.open(str(rotated)) as image:
        assert image.size != (100, 60)


def test_export_stars_real_cli(tmp_path):
    import json

    from astrostudio.adapters import SkyStackerAdapter
    from astrostudio.core.star_catalog import parse_star_catalog

    if shutil.which("skystacker") is None:
        return
    source = tmp_path / "stars.png"
    rgb = np.zeros((80, 80, 3), dtype="uint8")
    for x, y in ((20, 20), (60, 50), (40, 70)):
        rgb[y - 1:y + 2, x - 1:x + 2] = 255
    Image.fromarray(rgb, "RGB").save(str(source))
    output = tmp_path / "stars.json"
    argv = SkyStackerAdapter().build_export_stars_argv(str(source), str(output))
    subprocess.run(argv, check=True, timeout=90)
    data = json.loads(output.read_text())
    detections = parse_star_catalog(json.dumps(data))
    assert data["count"] >= 1
    assert len(detections) == data["count"]


def test_classify_objects_real_cli(tmp_path):
    import json

    if shutil.which("skystacker") is None:
        return
    from astrostudio.adapters import SkyStackerAdapter
    from astrostudio.core.object_classification import parse_classification

    source = tmp_path / "field.png"
    rgb = np.full((120, 120, 3), 10, dtype="uint8")
    rgb[40:80, 40:80] = 90
    Image.fromarray(rgb, "RGB").save(str(source))
    output = tmp_path / "objects.json"
    argv = SkyStackerAdapter().build_classify_objects_argv(str(source), str(output))
    subprocess.run(argv, check=True, timeout=90)
    objects, report = parse_classification(output.read_text())
    assert report["image"] == "field.png"
    assert len(objects) == report["count"]


def test_workspace_rotation_end_to_end_regenerates_preview(tmp_path, monkeypatch):
    from gi.repository import GLib
    from PIL import Image, ImageDraw

    from astrostudio.adapters import ImageMagickAdapter
    from astrostudio.core import ImageWorkspace, ProcessEngine, ScratchManager

    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    (tmp_path / "runtime").mkdir()
    source = tmp_path / "source.png"
    image = Image.new("RGB", (80, 60), "black")
    draw = ImageDraw.Draw(image)
    draw.rectangle((5, 5, 45, 20), fill="red")
    image.save(str(source))

    engine = ProcessEngine()
    workspace = ImageWorkspace(
        ScratchManager("session"), engine, ImageMagickAdapter(binary="convert")
    )
    opened = []
    workspace.prepare(str(source), opened.append, lambda m: pytest.fail(m))

    def wait_until(predicate, seconds=20):
        loop = GLib.MainLoop()

        def check():
            if predicate():
                loop.quit()
                return False
            return True

        GLib.timeout_add(50, check)
        GLib.timeout_add(seconds * 1000, loop.quit)
        loop.run()

    wait_until(lambda: bool(opened))
    assert opened
    working = opened[0]
    before = (Path(working.png_path)).read_bytes()

    rotated = []
    workspace.transform(
        working, {"rotate": "30"}, rotated.append, lambda m: pytest.fail(m)
    )
    wait_until(lambda: bool(rotated))
    assert rotated == [working]
    after = Path(working.png_path).read_bytes()
    assert after != before
    with Image.open(working.png_path) as preview:
        assert preview.size != (80, 60)


def test_skystaker_filter_pipeline_updates_working_image(tmp_path, monkeypatch):
    from gi.repository import GLib
    from PIL import Image

    from astrostudio.adapters import ImageMagickAdapter, SkyStackerAdapter
    from astrostudio.core import ImageWorkspace, ProcessEngine, ScratchManager

    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    (tmp_path / "runtime").mkdir()
    source = tmp_path / "starfield.png"
    image = Image.new("RGB", (96, 72), "black")
    for x in range(8, 88, 12):
        for y in range(8, 64, 12):
            image.putpixel((x, y), (255, 255, 255))
    image.save(str(source))

    engine = ProcessEngine()
    workspace = ImageWorkspace(
        ScratchManager("session"), engine, ImageMagickAdapter(binary="convert")
    )
    opened = []
    workspace.prepare(str(source), opened.append, lambda m: pytest.fail(m))

    def wait_until(predicate, seconds=60):
        loop = GLib.MainLoop()
        GLib.timeout_add(50, lambda: loop.quit() or False if predicate() else True)
        GLib.timeout_add(seconds * 1000, loop.quit)
        loop.run()

    wait_until(lambda: bool(opened))
    working = opened[0]
    before_tiff = Path(working.tiff_path).read_bytes()
    before_png = Path(working.png_path).read_bytes()
    done = []
    workspace.transform_via_image_op(
        working,
        SkyStackerAdapter(),
        "blur",
        ["--denoise-radius", "4"],
        done.append,
        lambda m: pytest.fail(m),
    )
    wait_until(lambda: bool(done))
    assert done == [working]
    assert Path(working.tiff_path).read_bytes() != before_tiff
    assert Path(working.png_path).read_bytes() != before_png
