"""Helpers for movable GTK top-level windows."""

import gi

gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gdk, Gtk  # noqa: E402


def make_draggable(window: Gtk.Window, handle: Gtk.Widget) -> None:
    """Drag a window by a header-like widget without changing child behaviour."""
    state = {"active": False, "x": 0.0, "y": 0.0, "ox": 0, "oy": 0}

    def on_press(_widget, event) -> bool:
        if event.button != 1:
            return False
        state["active"] = True
        state["x"] = event.x_root
        state["y"] = event.y_root
        state["ox"], state["oy"] = window.get_position()
        return True

    def on_motion(_widget, event) -> bool:
        if not state["active"]:
            return False
        window.move(
            int(state["ox"] + event.x_root - state["x"]),
            int(state["oy"] + event.y_root - state["y"]),
        )
        return True

    def on_release(_widget, _event) -> bool:
        state["active"] = False
        return False

    handle.add_events(
        Gdk.EventMask.BUTTON_PRESS_MASK
        | Gdk.EventMask.POINTER_MOTION_MASK
        | Gdk.EventMask.BUTTON_RELEASE_MASK
    )
    handle.connect("button-press-event", on_press)
    handle.connect("motion-notify-event", on_motion)
    handle.connect("button-release-event", on_release)
