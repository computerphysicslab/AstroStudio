"""Preview canvas helper tests."""

from astrostudio.ui.preview import selection_rectangle


def test_selection_rectangle_normalises_reversed_drag():
    assert selection_rectangle((100, 80), (40, 20)) == (40, 20, 60, 60)
    assert selection_rectangle((10, 10), (10, 10)) == (10, 10, 0, 0)
