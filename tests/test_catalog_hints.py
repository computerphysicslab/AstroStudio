"""Filename-driven plate-solving catalog hints."""

import os

from astrostudio.core.catalog_hints import (
    DEFAULT_CATALOG,
    extract_tokens,
    plate_center_argv,
    resolve_filename,
    unique_hint,
)


def test_extract_catalog_tokens():
    tokens, _normalized = extract_tokens("Orion-M42-NGC1976-IC434-C42.png")
    labels = [token for token, _source, _raw in tokens]
    assert set(labels) == {"M42", "NGC1976", "IC434", "C42"}


def test_bundled_catalog_resolves_m42():
    hint = unique_hint("Orion-M42-Riofrio-2026-11-09.png")
    assert hint is not None
    assert hint.obj.label == "M42"
    assert 83.7 < hint.obj.ra < 83.9
    assert -5.5 < hint.obj.dec < -5.2
    assert plate_center_argv(hint)[0] == "--plate-center"


def test_common_name_and_ngc_alias():
    by_name = unique_hint("Orion-Nebula-2026.png")
    by_ngc = unique_hint("NGC1976-Riofrio.png")
    assert by_name is not None and by_ngc is not None
    assert round(by_name.obj.ra, 3) == round(by_ngc.obj.ra, 3)
    assert round(by_name.obj.dec, 3) == round(by_ngc.obj.dec, 3)


def test_ambiguous_filename_has_no_unique_hint():
    hints = resolve_filename("M42-and-M31.png")
    coordinates = {(round(h.obj.ra, 3), round(h.obj.dec, 3)) for h in hints}
    assert len(coordinates) >= 2
    assert unique_hint("M42-and-M31.png") is None


def test_bundled_catalog_has_license_and_attribution():
    assert os.path.getsize(DEFAULT_CATALOG) > 100000
    data_dir = os.path.dirname(DEFAULT_CATALOG)
    assert os.path.isfile(os.path.join(data_dir, "CREDITS.md"))
    assert os.path.isfile(
        os.path.join(data_dir, "LICENSES", "OpenNGC-CC-BY-SA-4.0.txt")
    )
