"""Diffuse-object classification tests."""

import json

from astrostudio.adapters import SkyStackerAdapter
from astrostudio.core.object_classification import (
    parse_classification,
    write_object_layer_svg,
)


def test_classify_argv():
    assert SkyStackerAdapter().build_classify_objects_argv("a.jpg", "o.json") == [
        "skystacker", "--process-image", "a.jpg", "--classify-objects", "o.json",
        "--no-donation",
    ]


def test_parse_and_svg(tmp_path):
    payload = {
        "image": "a.jpg",
        "width": 100,
        "height": 80,
        "threshold_sigma": 3,
        "star_mask_pixels": 12,
        "count": 1,
        "objects": [{
            "id": 1, "x_px": 10, "y_px": 20, "area_px": 400, "flux": 100,
            "concentration": 2.1, "asymmetry": 0.4, "smoothness": 0.1,
            "gini": 0.3, "m20": -1.2, "ellipticity": 0.6,
            "object_type": "galaxy", "class_ucd": "src.class",
        }],
    }
    objects, report = parse_classification(json.dumps(payload))
    assert report["count"] == 1 and objects[0].object_type == "galaxy"
    path = write_object_layer_svg(str(tmp_path / "layer.svg"), objects, 100, 80)
    text = open(path, encoding="utf-8").read()
    assert 'id="diffuse-objects"' in text and "galaxy" in text
