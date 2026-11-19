"""Calibration folder discovery tests."""

from astrostudio.core.calibration import discover_calibration


def test_discover_calibration_folders(tmp_path):
    (tmp_path / "Lights").mkdir()
    (tmp_path / "Darks").mkdir()
    (tmp_path / "Bias").mkdir()
    (tmp_path / "Lights" / "a.fits").write_bytes(b"a")
    (tmp_path / "Darks" / "d.fits").write_bytes(b"d")
    (tmp_path / "Bias" / "b.fits").write_bytes(b"b")
    (tmp_path / "notes.txt").write_text("x")

    found = discover_calibration(str(tmp_path))
    assert len(found["light"]) == 1
    assert len(found["dark"]) == 1
    assert len(found["bias"]) == 1
    assert found["flat"] == []
