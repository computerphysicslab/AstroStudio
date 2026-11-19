"""FITS compression adapter tests."""

from astrostudio.adapters import FitsCompressionAdapter
from astrostudio.core.backends import BACKENDS


def test_fpack_and_gzip_argv():
    assert FitsCompressionAdapter("fpack").pack_argv("a.fits", "a.fz", "RICE_1") == [
        "fpack", "- RICE_1", "a.fits", "a.fz"
    ]
    assert FitsCompressionAdapter("gzip").pack_argv("a.fits", "a.gz") == [
        "gzip", "-kf", "a.fits"
    ]


def test_compression_backends_registered():
    names = {spec.name for spec in BACKENDS}
    assert {"FPack", "gzip"} <= names
