"""Annotation burn-in tests."""

from astrostudio.adapters import ImageMagickAdapter
from astrostudio.core.annotations import Annotation, build_annotate_argv, draw_command


def test_draw_commands():
    assert "line 1,2 3,4" in draw_command(Annotation("arrow", 1, 2, x2=3, y2=4))
    assert "circle 1,2 3,4" in draw_command(Annotation("circle", 1, 2, x2=3, y2=4))
    assert "text 1,2 'M42'" in draw_command(Annotation("label", 1, 2, "M42"))


def test_burn_in_argv():
    adapter = ImageMagickAdapter(binary="convert")
    argv = build_annotate_argv(adapter, "a.tiff", [Annotation("label", 1, 2, "M42")], "o.png")
    assert argv[0] == "convert"
    assert "-draw" in argv
    assert argv[-1] == "o.png"
