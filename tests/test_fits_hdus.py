"""FITS HDU inspection tests."""

from astrostudio.core.fits_hdus import inspect_fits


def header(cards):
    return "".join(card.ljust(80) for card in cards).encode("ascii").ljust(2880, b" ")


PRIMARY = [
    "SIMPLE  =                    T",
    "BITPIX  =                   16",
    "NAXIS   =                    2",
    "NAXIS1  =                    4",
    "NAXIS2  =                    4",
]
RGB = [
    "SIMPLE  =                    T",
    "BITPIX  =                   16",
    "NAXIS   =                    3",
    "NAXIS1  =                    4",
    "NAXIS2  =                    4",
    "NAXIS3  =                    3",
]
IMAGE_EXT = [
    "XTENSION= 'IMAGE   '",
    "BITPIX  =                   16",
    "NAXIS   =                    2",
    "NAXIS1  =                    4",
    "NAXIS2  =                    4",
]
BINTABLE_EXT = [
    "XTENSION= 'BINTABLE'",
    "BITPIX  =                    8",
    "NAXIS   =                    2",
    "NAXIS1  =                    8",
    "NAXIS2  =                    1",
]


def write(tmp_path, name, blocks):
    path = tmp_path / name
    path.write_bytes(b"".join(blocks))
    return str(path)


def _end(cards):
    return cards + ["END"]


def test_single_hdu_is_supported(tmp_path):
    path = write(tmp_path, "single.fits", [header(_end(PRIMARY)), b"\0" * 2880])
    info = inspect_fits(path)
    assert info["error"] is None
    assert len(info["hdus"]) == 1
    assert info["unusual"] is False


def test_rgb_primary_is_supported(tmp_path):
    path = write(tmp_path, "rgb.fits", [header(_end(RGB)), b"\0" * 2880])
    info = inspect_fits(path)
    assert info["error"] is None
    assert info["hdus"][0]["dimensions"] == (4, 4, 3)


def test_second_image_hdu_is_rejected(tmp_path):
    path = write(
        tmp_path,
        "multi.fits",
        [header(_end(PRIMARY)), b"\0" * 2880, header(_end(IMAGE_EXT)), b"\0" * 2880],
    )
    info = inspect_fits(path)
    assert info["unusual"] is True
    assert "single image HDU" in info["error"]


def test_bintable_is_rejected(tmp_path):
    path = write(
        tmp_path,
        "table.fits",
        [header(_end(PRIMARY)), b"\0" * 2880, header(_end(BINTABLE_EXT)), b"\0" * 2880],
    )
    info = inspect_fits(path)
    assert info["unusual"] is True
    assert "BINTABLE" in info["error"]


def test_inline_comments_are_stripped(tmp_path):
    cards = [
        "SIMPLE  =                    T / file does conform to FITS standard",
        "BITPIX  =                  -32 / IEEE floating point",
        "NAXIS   =                    2 / dimensionality of data",
        "NAXIS1  =                    4 / length of first axis",
        "NAXIS2  =                    4 / length of second axis",
        "OBJECT  = 'M42 / Orion'         / name with a slash inside quotes",
    ]
    path = write(tmp_path, "commented.fits", [header(_end(cards)), b"\0" * 2880])
    info = inspect_fits(path)
    assert info["error"] is None
    assert info["hdus"][0]["bitpix"] == -32
    assert info["hdus"][0]["dimensions"] == (4, 4)


def test_malformed_header_reports_error(tmp_path):
    path = write(tmp_path, "bad.fits", [b"not a fits header"])
    assert inspect_fits(path)["error"] is not None
