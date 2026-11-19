"""Window dragging helper tests."""

import os

import gi
import pytest

gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gdk, Gtk  # noqa: E402

from astrostudio.ui.window_utils import make_draggable  # noqa: E402

pytestmark = pytest.mark.skipif(
    not os.environ.get("DISPLAY"), reason="GTK display required"
)


def test_make_draggable_moves_window(monkeypatch):
    window = Gtk.Window()
    header = Gtk.HeaderBar()
    window.set_titlebar(header)
    moves = []
    monkeypatch.setattr(window, "move", lambda x, y: moves.append((x, y)))
    monkeypatch.setattr(window, "get_position", lambda: (100, 100))
    make_draggable(window, header)

    press = Gdk.Event.new(Gdk.EventType.BUTTON_PRESS)
    press.button, press.x_root, press.y_root = 1, 200, 200
    header.emit("button-press-event", press)
    motion = Gdk.Event.new(Gdk.EventType.MOTION_NOTIFY)
    motion.x_root, motion.y_root = 260, 230
    header.emit("motion-notify-event", motion)

    assert moves == [(160, 130)]
    window.destroy()
