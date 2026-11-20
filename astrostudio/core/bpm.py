"""Bad-pixel-map guards for calibration pipelines."""

from typing import Tuple

MAX_FRACTION = 0.001


def validate_bpm_count(bad_pixels: int, total_pixels: int, max_fraction: float = MAX_FRACTION) -> Tuple[bool, str]:
    """Return (accepted, message) for a bad-pixel map count."""
    if total_pixels <= 0:
        return False, "Unknown sensor size"
    fraction = bad_pixels / total_pixels
    if fraction > max_fraction:
        return False, "BPM flags %.4f%% (> %.3f%%)" % (fraction * 100, max_fraction * 100)
    return True, "BPM flags %.4f%%" % (fraction * 100)
