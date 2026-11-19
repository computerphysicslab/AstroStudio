"""Optional external pipeline adapter tests."""

from astrostudio.adapters import ExternalToolAdapter, ImageMagickAdapter


def test_raw_developers():
    assert ExternalToolAdapter("rawtherapee-cli").develop_raw("a.raw", "o.tiff") == [
        "rawtherapee-cli", "-o", "o.tiff", "a.raw"
    ]
    assert ExternalToolAdapter("dcraw_emu").develop_raw("a.raw", "o.tiff")[-1] == "a.raw"


def test_panorama_fuse_and_gimp():
    adapter = ExternalToolAdapter("gimp")
    assert adapter.panorama(["a.jpg", "b.jpg"], "o.tif") == [
        "gimp", "-o", "o.tif", "a.jpg", "b.jpg"
    ]
    assert adapter.fuse(["a.tif"], "o.tif")[0] == "gimp"
    assert adapter.gimp_script("(gimp-quit 0)")[-1] == "(gimp-quit 0)"


def test_diff_argv():
    argv = ImageMagickAdapter(binary="convert").build_diff_argv("a.tiff", "b.tiff", "d.png")
    assert "-compose" in argv and "difference" in argv
    assert argv[-1] == "d.png"
