"""CLI adapter tests."""

from astrostudio.adapters import ExifToolAdapter, ImageMagickAdapter


def test_imagemagick_argv_and_output_path():
    adapter = ImageMagickAdapter()
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


def test_exiftool_argv_contains_metadata_fields():
    adapter = ExifToolAdapter()
    argv = adapter.build_argv(["/data/light.fits", "/data/light2.fits"])
    assert argv[0] == "exiftool"
    assert "-T" in argv
    for field in ("-filename", "-exptime", "-iso", "-fnumber", "-datetimeoriginal"):
        assert field in argv
    assert argv[-2:] == ["/data/light.fits", "/data/light2.fits"]


def test_adapters_report_missing_binary(monkeypatch):
    import astrostudio.adapters.base as base

    monkeypatch.setattr(base.shutil, "which", lambda binary: None)
    assert not ImageMagickAdapter().is_available()
    assert not ExifToolAdapter().is_available()
