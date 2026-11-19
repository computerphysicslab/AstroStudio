"""Parameter suggestion tests."""

from astrostudio.core.presets import parse_metadata_text, suggest_presets


def test_parse_and_suggest():
    meta = parse_metadata_text("ISO : 3200\nExposureTime : 1/20\n")
    assert meta["ISO"] == "3200"
    lines = suggest_presets(meta)
    assert any("Denoise" in line for line in lines)
    assert any("Sharpen" in line for line in lines)
