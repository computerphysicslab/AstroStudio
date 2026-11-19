"""WCS sidecar tests."""

import json
import math

from astrostudio.core.wcs import wcs_cards, write_wcs_sidecar

SOLUTION = {
    "WCS": {
        "CRVAL1": math.radians(83.822),
        "CRVAL2": math.radians(-5.391),
        "CRPIX1": 0,
        "CRPIX2": 0,
        "CD": [[math.radians(-0.01), 0], [0, math.radians(0.01)]],
    },
    "Method": "native",
}


def test_wcs_cards_conversion():
    cards = wcs_cards(SOLUTION)
    assert round(cards["CRVAL1"], 3) == 83.822
    assert cards["CRPIX1"] == 1.0
    assert round(cards["CD1_1"], 4) == -0.01


def test_sidecar_written(tmp_path):
    fits = tmp_path / "out.fits"
    fits.write_bytes(b"fits")
    path = write_wcs_sidecar(str(fits), SOLUTION)
    assert path.endswith("out.wcs.json")
    assert json.loads(open(path).read())["METHOD"] == "native"


def test_overlay_center_is_zero_based():
    from astrostudio.core.wcs import overlay_center

    assert overlay_center(SOLUTION) == (0.0, 0.0)
