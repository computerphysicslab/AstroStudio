"""Star catalog parsing and SVG layer tests."""

import json

from astrostudio.adapters import SkyStackerAdapter
from astrostudio.core.star_catalog import (
    parse_star_catalog,
    write_star_layer_svg,
)


def test_export_stars_argv():
    assert SkyStackerAdapter().build_export_stars_argv("a.jpg", "stars.json") == [
        "skystacker", "--process-image", "a.jpg", "--export-stars", "stars.json",
        "--no-donation",
    ]


def test_parse_json_and_csv():
    payload = {
        "stars": [
            {"x_px": 10, "y_px": 20, "flux": 90, "size_px": 4, "eccentricity": 0.1, "hfr_px": 2},
            {"x_px": 30, "y_px": 40, "flux": 10, "size_px": 3, "eccentricity": 0.2, "hfr_px": 3},
        ]
    }
    detections = parse_star_catalog(json.dumps(payload))
    assert len(detections) == 2 and detections[0].flux == 90
    csv_text = "x_px,y_px,flux,size_px,eccentricity,hfr_px\n1,2,5,3,0.1,2\n"
    assert parse_star_catalog(csv_text, ".csv")[0].x == 1


def test_svg_layer(tmp_path):
    payload = {"stars": [{"x_px": 5, "y_px": 6, "flux": 1}]}
    detections = parse_star_catalog(json.dumps(payload))
    path = write_star_layer_svg(str(tmp_path / "layer.svg"), detections, 100, 80)
    content = open(path, encoding="utf-8").read()
    assert 'id="star-identification"' in content
    assert "<circle" in content
