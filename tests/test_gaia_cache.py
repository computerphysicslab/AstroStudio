"""Gaia cache helper tests."""

from astrostudio.core.gaia_cache import gaia_flags, tile_count


def test_tile_count_and_flags(tmp_path):
    (tmp_path / "tile.json").write_text("{}")
    (tmp_path / "other.txt").write_text("x")
    assert tile_count(str(tmp_path)) == 1
    assert gaia_flags(str(tmp_path), 64, True) == [
        "--gaia-nside", "64", "--gaia-cache-dir", str(tmp_path), "--gaia-offline"
    ]
