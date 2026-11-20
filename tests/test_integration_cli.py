"""Real-CLI integration tests (skipped when ImageMagick is absent)."""

import shutil
import subprocess

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
