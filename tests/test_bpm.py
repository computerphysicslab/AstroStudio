"""Bad pixel map guard tests."""

from astrostudio.adapters import SkyStackerAdapter
from astrostudio.core.bpm import validate_bpm_count


def test_bpm_cap():
    ok, _ = validate_bpm_count(100, 1_000_000)
    assert ok
    bad, message = validate_bpm_count(2000, 1_000_000)
    assert not bad and ">" in message


def test_bpm_argv():
    argv = SkyStackerAdapter().build_bpm_argv("/lights", "/out", 6.0)
    assert "--bpm-auto" in argv
    assert argv[argv.index("--bpm-auto-sigma") + 1] == "6.0"
