"""Frame quality parser tests."""

from astrostudio.core.frame_quality import parse_measurements


def test_parse_measurements():
    text = (
        '{"images":[{"file":"a.fits","width":100,"height":80,"stars":50,'
        '"median_hfr_px":1.2,"median_eccentricity":0.1,"bg_sigma":0.01,'
        '"snr":30.5,"quality":88.2}]}'
    )
    result = parse_measurements(text)
    assert len(result) == 1
    assert result[0].file == "a.fits"
    assert result[0].snr == 30.5
    assert parse_measurements("bad json") == []
