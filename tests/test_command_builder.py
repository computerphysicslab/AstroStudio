"""Sanitized argv serialization tests."""

import pytest

from astrostudio.core.command_builder import CommandBuilder


def test_build_flags_in_declared_order_with_separate_arguments():
    builder = CommandBuilder(
        "magick",
        flag_specs=(
            ("-crop", "crop", None),
            ("-resize", "resize", None),
            ("-unsharp", "unsharp", None),
        ),
    )
    argv = builder.build(
        ["/path with spaces/input file.jpg"],
        "/tmp/out.png",
        {"crop": "800x600+0+0", "resize": "50%", "unsharp": "1.5x1+0.7+0.02"},
    )
    assert argv == [
        "magick",
        "-crop",
        "800x600+0+0",
        "-resize",
        "50%",
        "-unsharp",
        "1.5x1+0.7+0.02",
        "/path with spaces/input file.jpg",
        "/tmp/out.png",
    ]


def test_boolean_flags_defaults_and_missing_values():
    builder = CommandBuilder(
        "exiftool",
        flag_specs=(("-T", "tabular", None), ("-a", "all", None)),
        defaults={"tabular": True},
    )
    assert builder.build(["a.fits"], params={"all": False}) == [
        "exiftool",
        "-T",
        "a.fits",
    ]
    assert builder.build(["a.fits"], params={"all": True}) == [
        "exiftool",
        "-T",
        "-a",
        "a.fits",
    ]


def test_formatter_and_none_parameters_are_applied():
    builder = CommandBuilder(
        "tool",
        flag_specs=(("--level", "level", lambda value: "%.2f" % value),),
        defaults={"level": 1.0},
    )
    assert builder.build([], params={"level": 0.5, "ignored": None}) == [
        "tool",
        "--level",
        "0.50",
    ]


def test_formatter_can_expand_one_flag_into_several_argv_tokens():
    builder = CommandBuilder(
        "convert",
        flag_specs=(("-morphology", "morphology", lambda value: value.split()),),
    )
    assert builder.build(["in.tiff"], "out.tiff", {"morphology": "Erode Disk:1"}) == [
        "convert",
        "-morphology",
        "Erode",
        "Disk:1",
        "in.tiff",
        "out.tiff",
    ]


def test_nul_bytes_are_rejected():
    builder = CommandBuilder("tool", flag_specs=(("-x", "x", None),))
    with pytest.raises(ValueError):
        builder.build(["/tmp/\x00bad"])
    with pytest.raises(ValueError):
        builder.build([], output="/tmp/\x00out")
    with pytest.raises(ValueError):
        CommandBuilder("")


def test_nul_in_argument_value_is_rejected():
    builder = CommandBuilder("tool", flag_specs=(("-x", "x", None),))
    with pytest.raises(ValueError):
        builder.build([], params={"x": "bad\x00value"})
