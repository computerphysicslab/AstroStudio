"""Read-only histogram chart drawn from CLI-provided text data."""

import gi

gi.require_version("Gdk", "3.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gdk, GLib, Gtk  # noqa: E402


class HistogramWidget(Gtk.DrawingArea):
    """Overlay distributions and expose two draggable stretch cut points."""

    def __init__(self) -> None:
        super().__init__()
        self.datasets: list = []
        self.low = 0.0
        self.high = 255.0
        self.on_change = None
        self._drag = None
        self._apply_timer = None
        self._last_applied = (self.low, self.high)
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
        self._last_applied = (self.low, self.high)
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
        if changed:
            self._schedule_apply()
        self.queue_draw()

    def _schedule_apply(self) -> None:
        if self._apply_timer is not None:
            return
        self._apply_timer = GLib.timeout_add(1000, self._debounced_apply)

    def _debounced_apply(self) -> bool:
        self._apply_timer = None
        current = (self.low, self.high)
        if self._drag is not None and current != self._last_applied and self.on_change:
            self._last_applied = current
            self.on_change(*current)
        return False

    def _apply_now(self) -> None:
        if self._apply_timer is not None:
            GLib.source_remove(self._apply_timer)
            self._apply_timer = None
        current = (self.low, self.high)
        if current != self._last_applied and self.on_change is not None:
            self._last_applied = current
            self.on_change(*current)

    def _on_press(self, _widget, event) -> bool:
        width = self.get_allocated_width()
        height = self.get_allocated_height()
        if width <= 0:
            return False
        low_x = self._handle_x(self.low, width)
        high_x = self._handle_x(self.high, width)
        if event.y > height - 22:
            self._drag = "low" if abs(event.x - low_x) <= abs(event.x - high_x) else "high"
        else:
            self._drag = self._nearest_handle(event.x, width)
        self._move_handle(event.x, width)
        return True

    def _on_motion(self, _widget, event) -> bool:
        if self._drag is None:
            return False
        self._move_handle(event.x, self.get_allocated_width())
        return True

    def _on_release(self, _widget, _event) -> bool:
        if self._drag is not None:
            self._apply_now()
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

        loupe_x = width * 0.58
        loupe_w = width * 0.38
        cr.set_source_rgba(1.0, 0.85, 0.2, 0.6)
        cr.rectangle(loupe_x, 6, loupe_w, 48)
        cr.stroke()
        shadow = [(x, count) for _label, _colour, points in self.datasets for x, count in points if x <= 13]
        if shadow:
            peak = max(count for _x, count in shadow) or 1
            cr.set_source_rgb(1.0, 0.85, 0.2)
            for x, count in shadow:
                px = loupe_x + (x / 13.0) * loupe_w
                ph = (count / peak) * 48
                cr.move_to(px, 54)
                cr.line_to(px, 54 - ph)
            cr.stroke()

        max_log = 1.0
        prepared = []
        for label, colour, points in self.datasets:
            prepared.append((label, colour, [(x, math.log10(1 + count)) for x, count in points]))
            for _x, value in prepared[-1][2]:
                max_log = max(max_log, value)

        for label, colour, points in prepared:
            if not points:
                continue
            cr.set_source_rgba(*colour, 0.30)
            cr.move_to(points[0][0] / 255.0 * width, height)
            for intensity, value in points:
                cr.line_to(
                    intensity / 255.0 * width,
                    height - value / max_log * (height - 8),
                )
            cr.line_to(points[-1][0] / 255.0 * width, height)
            cr.close_path()
            cr.fill()
            cr.set_source_rgba(*colour, 0.85)
            cr.set_line_width(1.5)
            for intensity, value in points:
                x = intensity / 255.0 * width
                bar_height = value / max_log * (height - 8)
                cr.rectangle(x, height - bar_height, max(width / 200.0, 2.0), bar_height)
                cr.fill()

        if not prepared:
            cr.set_source_rgb(0.7, 0.7, 0.7)
            cr.set_font_size(11)
            cr.move_to(10, height / 2)
            cr.show_text("Press View > Histogram to compute distributions")

        for value, colour in ((self.low, (0.20, 0.85, 1.0)), (self.high, (1.0, 0.65, 0.20))):
            x = self._handle_x(value, width)
            cr.set_source_rgba(*colour, 0.95)
            cr.set_line_width(2.0)
            cr.move_to(x, 0)
            cr.line_to(x, height)
            cr.stroke()
            grip_x = max(8.0, min(width - 8.0, x))
            cr.move_to(grip_x - 6, height - 2)
            cr.line_to(grip_x + 6, height - 2)
            cr.line_to(grip_x, height - 14)
            cr.close_path()
            cr.fill()

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
