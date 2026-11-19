"""Save As naming tests."""

from pathlib import Path

from astrostudio.core.export_paths import unique_export_path


def test_prefers_plain_name_and_increments_on_collisions(tmp_path):
    assert unique_export_path(str(tmp_path), "light", "tif") == str(
        tmp_path / "light.tif"
    )
    (tmp_path / "light.tif").write_bytes(b"a")
    assert unique_export_path(str(tmp_path), "light", "tif") == str(
        tmp_path / "light-1.tif"
    )
    (tmp_path / "light-1.tif").write_bytes(b"b")
    (tmp_path / "light-2.tif").write_bytes(b"c")
    (tmp_path / "light-3.tif").write_bytes(b"d")
    assert unique_export_path(str(tmp_path), "light", "tif") == str(
        tmp_path / "light-4.tif"
    )


def test_extension_is_normalised(tmp_path):
    assert unique_export_path(str(tmp_path), "M42", ".fits") == str(
        tmp_path / "M42.fits"
    )
