"""Linear-space guard tests."""

from astrostudio.core.linear_guard import check_linear_guard


def test_guard_blocks_after_stretch():
    ok, _ = check_linear_guard(["resize"])
    assert ok
    blocked, reason = check_linear_guard(["stretch", "deconvolve"])
    assert not blocked and "non-linear" in reason
    allowed, _ = check_linear_guard(["stretch", "deconvolve"], allow_override=True)
    assert allowed
