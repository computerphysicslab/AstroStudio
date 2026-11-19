"""CLI histogram text parsing tests."""

from astrostudio.core.histogram import histogram_argv, parse_histogram_text


def test_histogram_argv_limits_output_size():
    argv = histogram_argv("convert", "big.tiff")
    assert argv == [
        "convert",
        "big.tiff",
        "-resize",
        "256x256!",
        "-colors",
        "256",
        "-format",
        "%c",
        "histogram:info:-",
    ]


def test_parse_histogram_text_aggregates_by_luminance():
    text = """\
       2: ( 10, 20, 30) #0A141E srgb(10,20,30)
       3: ( 10, 20, 30) #0A141E srgb(10,20,30)
       7: (200,200,200) #C8C8C8 gray(200)
noise line
"""
    assert parse_histogram_text(text) == [(20, 5), (200, 7)]


def test_empty_text_is_safe():
    assert parse_histogram_text("") == []
