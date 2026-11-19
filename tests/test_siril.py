"""Siril adapter tests."""

from astrostudio.adapters import SirilAdapter


def test_siril_argv_and_scripts():
    adapter = SirilAdapter()
    assert adapter.build_script_argv("/tmp/job.ssf") == ["siril-cli", "-s", "/tmp/job.ssf"]
    script = adapter.calibration_script("/lights", "/darks", "", "/biases", "/out")
    assert 'cd "/lights"' in script
    assert "calibrate light" in script
    assert "stack median result" in script
    assert adapter.stacking_script("/lights", "/out") .startswith("requires siril-cli")
