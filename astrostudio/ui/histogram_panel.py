"""Read-only histogram chart drawn from CLI-provided text data."""

import gi

gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gdk, Gtk  # noqa: E402


class HistogramWidget(Gtk.DrawingArea):
    """Overlay distributions and expose two draggable stretch cut points."""

    def __init__(self) -> None:
        super().__init__()
        self.datasets: list = []
        self.low = 0.0
        self.high = 255.0
        self.on_change = None
        self._drag = None
        self.set_app_paintable(True)
        self.set_size_request(320, 140)
        self.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
        )
        self.connect("draw", self._on_draw)
        self.connect("button-press-event", self._on_press)
        self.connect("motion-notify-event", self._on_motion)
        self.connect("button-release-event", self._on_release)

    def set_datasets(self, datasets: list) -> None:
        self.datasets = datasets
        self.queue_draw()

    def set_points(self, low: float, high: float) -> None:
        self.low = max(0.0, min(low, high - 5.0))
        self.high = max(self.low + 5.0, min(high, 255.0))
        self.queue_draw()

    def _handle_x(self, value: float, width: int) -> float:
        return value / 255.0 * width

    def _nearest_handle(self, x: float, width: int) -> str:
        return (
            "low"
            if abs(x - self._handle_x(self.low, width))
            <= abs(x - self._handle_x(self.high, width))
            else "high"
        )

    def _move_handle(self, x: float, width: int) -> None:
        value = max(0.0, min(255.0, x / width * 255.0))
        if self._drag == "low":
            new_low = min(value, self.high - 5.0)
            changed = new_low != self.low
            self.low = new_low
        else:
            new_high = max(value, self.low + 5.0)
            changed = new_high != self.high
            self.high = new_high
        if changed and self.on_change is not None:
            self.on_change(self.low, self.high)
        self.queue_draw()

    def _on_press(self, _widget, event) -> bool:
        width = self.get_allocated_width()
        if width <= 0:
            return False
        self._drag = self._nearest_handle(event.x, width)
        self._move_handle(event.x, width)
        return True

    def _on_motion(self, _widget, event) -> bool:
        if self._drag is None:
            return False
        self._move_handle(event.x, self.get_allocated_width())
        return True

    def _on_release(self, _widget, _event) -> bool:
        self._drag = None
        return False

    def _on_draw(self, _widget, cr) -> bool:
        import math

        width = self.get_allocated_width()
        height = self.get_allocated_height()
        cr.set_source_rgb(0.06, 0.06, 0.08)
        cr.paint()

        cr.set_source_rgba(1.0, 1.0, 1.0, 0.18)
        cr.set_line_width(1.0)
        for row in range(1, 5):
            y = height * row / 5.0
            cr.move_to(0, y)
            cr.line_to(width, y)
            cr.stroke()

        max_log = 1.0
        prepared = []
        for label, colour, points in self.datasets:
            prepared.append((label, colour, [(x, math.log10(1 + count)) for x, count in points]))
            for _x, value in prepared[-1][2]:
                max_log = max(max_log, value)

        for label, colour, points in prepared:
            cr.set_source_rgba(*colour, 0.65)
            for intensity, value in points:
                x = intensity / 255.0 * width
                bar_height = value / max_log * (height - 8)
                cr.rectangle(x, height - bar_height, max(width / 255.0, 1.0), bar_height)
                cr.fill()

        for value, colour in ((self.low, (0.20, 0.85, 1.0)), (self.high, (1.0, 0.65, 0.20))):
            x = self._handle_x(value, width)
            cr.set_source_rgba(*colour, 0.95)
            cr.set_line_width(2.0)
            cr.move_to(x, 0)
            cr.line_to(x, height)
            cr.stroke()

        cr.set_source_rgb(0.9, 0.9, 0.9)
        cr.set_font_size(10)
        for index, (label, colour, _points) in enumerate(prepared):
            cr.rectangle(8, 8 + index * 14, 10, 10)
            cr.set_source_rgba(*colour, 0.9)
            cr.fill()
            cr.set_source_rgb(0.9, 0.9, 0.9)
            cr.move_to(22, 17 + index * 14)
            cr.show_text(label)
        return False
