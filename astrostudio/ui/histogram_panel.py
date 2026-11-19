"""Read-only histogram chart drawn from CLI-provided text data."""

import gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk  # noqa: E402


class HistogramWidget(Gtk.DrawingArea):
    """Overlay two 0-255 distributions with a logarithmic count axis."""

    def __init__(self) -> None:
        super().__init__()
        self.datasets: list = []
        self.set_app_paintable(True)
        self.set_size_request(640, 280)
        self.connect("draw", self._on_draw)

    def set_datasets(self, datasets: list) -> None:
        self.datasets = datasets
        self.queue_draw()

    def _on_draw(self, _widget, cr) -> bool:
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

        import math

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

        cr.set_source_rgb(0.9, 0.9, 0.9)
        for index, (label, colour, _points) in enumerate(prepared):
            cr.rectangle(12, 12 + index * 18, 12, 12)
            cr.set_source_rgba(*colour, 0.9)
            cr.fill()
            cr.set_source_rgb(0.9, 0.9, 0.9)
            cr.move_to(30, 22 + index * 18)
            cr.show_text(label)
        return False
