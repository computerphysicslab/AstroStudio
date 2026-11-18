"""Export format catalog tests."""

from astrostudio.core.export_formats import EXPORT_FORMATS, find_format


def test_catalog_covers_scientific_and_display_formats():
    keys = {item.key for item in EXPORT_FORMATS}
    assert {
        "tiff16",
        "tiff16-lzw",
        "tiff16-zip",
        "fits16",
        "png8",
        "jpg90",
        "jpg95",
        "bmp8",
    } <= keys


def test_compression_flags_are_serialized():
    assert find_format("tiff16-lzw").flags == ("-depth", "16", "-compress", "LZW")
    assert find_format("jpg90").flags == ("-depth", "8", "-quality", "90")
    assert find_format("fits16").extension == "fits"


def test_unknown_key_falls_back_to_first_format():
    assert find_format("missing").key == EXPORT_FORMATS[0].key
