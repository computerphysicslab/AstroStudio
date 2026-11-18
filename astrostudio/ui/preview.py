"""Read-only image preview surface for backend output files."""

import gi

gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gdk, GdkPixbuf, Gtk  # noqa: E402


class PreviewPane(Gtk.DrawingArea):
    """Display-only canvas; image data is never modified here."""

    def __init__(self) -> None:
        super().__init__()
        self.pixbuf: GdkPixbuf.Pixbuf = None
        self.path = None
        self.zoom = 1.0
        self.fit = True
        self.set_app_paintable(True)
        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.connect("draw", self._on_draw)

    def load(self, path: str) -> None:
        self.set_pixbuf(GdkPixbuf.Pixbuf.new_from_file(path), path)

    def set_pixbuf(self, pixbuf: GdkPixbuf.Pixbuf, path: str = None) -> None:
        self.pixbuf = pixbuf
        self.path = path
        self.fit = True
        self.zoom = 1.0
        self.queue_draw()

    def clear(self) -> None:
        self.pixbuf = None
        self.path = None
        self.queue_draw()

    def zoom_in(self) -> None:
        self.fit = False
        self.zoom = min(self.zoom * 1.25, 32.0)
        self.queue_draw()

    def zoom_out(self) -> None:
        self.fit = False
        self.zoom = max(self.zoom / 1.25, 0.05)
        self.queue_draw()

    def zoom_fit(self) -> None:
        self.fit = True
        self.zoom = 1.0
        self.queue_draw()

    def set_zoom_scale(self, scale: float) -> None:
        self.fit = False
        self.zoom = min(max(scale, 0.01), 32.0)
        self.queue_draw()

    def _view_parameters(self):
        allocation = self.get_allocation()
        if self.pixbuf is None:
            return allocation, 1.0, 0.0, 0.0
        width = self.pixbuf.get_width()
        height = self.pixbuf.get_height()
        if self.fit:
            scale = min(allocation.width / width, allocation.height / height)
        else:
            scale = self.zoom
        offset_x = (allocation.width - width * scale) / 2.0
        offset_y = (allocation.height - height * scale) / 2.0
        return allocation, scale, offset_x, offset_y

    def image_coordinates(self, x: float, y: float):
        _, scale, offset_x, offset_y = self._view_parameters()
        if self.pixbuf is None or scale <= 0:
            return None
        column = int((x - offset_x) / scale)
        row = int((y - offset_y) / scale)
        if 0 <= column < self.pixbuf.get_width() and 0 <= row < self.pixbuf.get_height():
            return column, row
        return None

    def _on_draw(self, widget, cr) -> bool:
        allocation, scale, offset_x, offset_y = self._view_parameters()
        cr.set_source_rgb(0.07, 0.07, 0.09)
        cr.paint()
        if self.pixbuf is None:
            return False
        cr.save()
        cr.translate(offset_x, offset_y)
        cr.scale(scale, scale)
        Gdk.cairo_set_source_pixbuf(cr, self.pixbuf, 0, 0)
        cr.paint()
        cr.restore()
        return False
