"""Quality dashboard parsing tests."""

import json

from astrostudio.core.quality_dashboard import parse_quality_report, summarize


def test_parse_json_report_and_summarize():
    report = {
        "operation": "measure-quality",
        "images": [{
            "file": "light1.fits", "width": 100, "height": 100, "stars": 80,
            "median_hfr_px": 2.1, "median_eccentricity": 0.3, "bg_sigma": 1.0,
            "snr": 35.0, "quality": 88.0,
        }],
    }
    rows = parse_quality_report(json.dumps(report))
    assert len(rows) == 1
    passed, issues = summarize(rows)
    assert passed and not issues


def test_csv_report_flags_low_quality():
    text = (
        "file,width,height,stars,median_hfr_px,median_eccentricity,bg_sigma,snr,quality\n"
        "bad.fits,100,100,10,4.5,0.9,2.0,5.0,30\n"
    )
    rows = parse_quality_report(text)
    passed, issues = summarize(rows)
    assert not passed
    assert any("low SNR" in issue for issue in issues)
    assert any("high HFR" in issue for issue in issues)
