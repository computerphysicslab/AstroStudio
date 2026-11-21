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


def _solution_object():
    from astrostudio.core.plate_solution import PlateSolution

    return PlateSolution(
        ra_deg=83.822,
        dec_deg=-5.391,
        scale_arcsec_per_px=1.5,
        fov_width_deg=0.5,
        fov_height_deg=0.4,
        orientation_deg=0.0,
        method="header",
        rms_arcsec=0.6,
        matches=96,
        stars=200,
        path="/tmp/plate_solution.json",
    )


def test_metadata_merge_adds_missing_tags_and_keeps_existing():
    from astrostudio.core.metadata_enrichment import merge_metadata, proposed_tags

    existing = {"EXPOSURE": 30, "OBJECT": "M42", "RA_DEG": 83.822}
    merged, added, conflicts = merge_metadata(existing, proposed_tags(_solution_object()))
    assert merged["EXPOSURE"] == 30
    assert merged["OBJECT"] == "M42"
    assert "RA_DEG" not in added
    assert "DEC_DEG" in added
    assert conflicts == []


def test_metadata_merge_reports_conflicts_without_overwriting():
    from astrostudio.core.metadata_enrichment import merge_metadata, proposed_tags

    merged, _added, conflicts = merge_metadata(
        {"RA_DEG": 10.0}, proposed_tags(_solution_object())
    )
    assert merged["RA_DEG"] == 10.0
    assert "RA_DEG" in conflicts


def test_metadata_sidecar_round_trip(tmp_path):
    from astrostudio.core.metadata_enrichment import (
        load_sidecar,
        write_metadata_sidecar,
    )

    path = write_metadata_sidecar(
        str(tmp_path), "capture", {"RA_DEG": 83.822}, ["RA_DEG"], [], "/tmp/s.json"
    )
    assert path.endswith("capture.metadata.json")
    data = json.loads(open(path, encoding="utf-8").read())
    assert data["source"] == "s.json"
    assert load_sidecar(str(tmp_path), "capture") == {"RA_DEG": 83.822}


def test_overlay_center_is_zero_based():
    from astrostudio.core.wcs import overlay_center

    assert overlay_center(SOLUTION) == (0.0, 0.0)
