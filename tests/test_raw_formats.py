"""RAW/DNG warning tests."""

from astrostudio.core.raw_formats import raw_warnings


def test_lossy_warning():
    warnings = raw_warnings({"Compression": "JPEG", "CFAPattern": "RGGB"})
    assert any("Lossy" in item for item in warnings)
    assert any("RGGB" in item for item in warnings)


def test_linear_dng_warning():
    warnings = raw_warnings({"DNGCompression": "Linear Raw"})
    assert any("Linear DNG" in item for item in warnings)
