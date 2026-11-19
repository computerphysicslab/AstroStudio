"""Direct ASTAP/solve-field adapter tests."""

from astrostudio.adapters.astrometry import AstrometryAdapter, scale_hint_arcsec


def test_scale_hint():
    assert round(scale_hint_arcsec("50", "4.3"), 2) == 17.74


def test_solve_field_argv_with_seed_and_hint():
    adapter = AstrometryAdapter("solve-field")
    argv = adapter.build_solve_field_argv("a.jpg", "/tmp/out", "83.8", "-5.3", scale="8.0")
    assert argv[0] == "solve-field"
    assert "--ra" in argv and "--dec" in argv
    assert "--scale-units" in argv
    assert argv[-1] == "a.jpg"


def test_astap_argv():
    argv = AstrometryAdapter("astap").build_astap_argv("a.jpg", "/tmp/out", "8")
    assert argv == ["astap", "-f", "a.jpg", "-D", "/tmp/out", "-fov", "8"]
