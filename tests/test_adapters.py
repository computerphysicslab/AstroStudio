"""CLI adapter tests."""

from astrostudio.adapters import ExifToolAdapter, ImageMagickAdapter
from astrostudio.core.export_formats import find_format


def test_imagemagick_argv_and_output_path():
    adapter = ImageMagickAdapter(binary="magick")
    assert adapter.binary == "magick"
    argv = adapter.build_argv(
        ["/data/M42 capture.cr2"],
        "/tmp/job/M42_processed.png",
        {"resize": "50%", "unsharp": "1.5x1+0.7+0.02"},
    )
    assert argv == [
        "magick",
        "-resize",
        "50%",
        "-unsharp",
        "1.5x1+0.7+0.02",
        "/data/M42 capture.cr2",
        "/tmp/job/M42_processed.png",
    ]
    assert (
        adapter.output_path("/tmp/job", "/data/M42 capture.cr2", "tif")
        == "/tmp/job/M42_capture_processed.tif"
    )
    assert adapter.supports_input("capture.JPG")
    assert not adapter.supports_input("capture.cr2")


def test_imagemagick_workspace_argv_uses_tiff_and_png():
    adapter = ImageMagickAdapter(binary="convert")
    assert list(adapter.build_import_argv("/data/light.png", "/tmp/job/working.tiff")) == [
        "convert",
        "/data/light.png",
        "-depth",
        "16",
        "/tmp/job/working.tiff",
    ]
    assert list(adapter.build_preview_argv("/tmp/job/working.tiff", "/tmp/job/preview.png")) == [
        "convert",
        "/tmp/job/working.tiff",
        "-depth",
        "8",
        "/tmp/job/preview.png",
    ]
    assert adapter.build_export_argv("/tmp/job/working.tiff", "/tmp/out.tif") == [
        "convert",
        "/tmp/job/working.tiff",
        "/tmp/out.tif",
    ]
    assert adapter.build_export_argv(
        "/tmp/job/working.tiff", "/tmp/out.jpg", find_format("jpg90")
    ) == [
        "convert",
        "/tmp/job/working.tiff",
        "-depth",
        "8",
        "-quality",
        "90",
        "/tmp/out.jpg",
    ]


def test_exiftool_argv_contains_canonical_metadata_fields():
    adapter = ExifToolAdapter()
    argv = adapter.build_argv(["/data/light.fits", "/data/light2.fits"])
    assert argv[0] == "exiftool"
    assert argv[1] == "-s"
    for field in ("-ExposureTime", "-ISO", "-FNumber", "-DateTimeOriginal", "-BitsPerSample"):
        assert field in argv
    assert argv[-2:] == ["/data/light.fits", "/data/light2.fits"]


def test_adapters_report_missing_binary(monkeypatch):
    import astrostudio.adapters.base as base

    monkeypatch.setattr(base.shutil, "which", lambda binary: None)
    assert not ImageMagickAdapter(binary="magick").is_available()
    assert not ExifToolAdapter().is_available()


def test_imagemagick_adapter_falls_back_to_convert(monkeypatch):
    import astrostudio.adapters.magick as magick

    monkeypatch.setattr(magick.shutil, "which", lambda binary: "/usr/bin/convert" if binary == "convert" else None)
    assert ImageMagickAdapter().binary == "convert"
