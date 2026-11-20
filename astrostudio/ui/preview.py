"""Read-only image preview surface for backend output files."""

import math

import gi

gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gdk, GdkPixbuf, GLib, Gtk  # noqa: E402

from ..core.preview_pyramid import choose_level
from ..core.star_catalog import star_display_radius


def selection_rectangle(start, end):
    """Return a normalised (x, y, width, height) rectangle from two points."""
    x1, y1 = start
    x2, y2 = end
    return min(x1, x2), min(y1, y2), abs(x2 - x1), abs(y2 - y1)


class PreviewPane(Gtk.DrawingArea):
    """Display-only canvas; image data is never modified here."""

    def __init__(self) -> None:
        super().__init__()
        self.pixbuf: GdkPixbuf.Pixbuf = None
        self.path = None
        self.zoom = 1.0
        self.fit = True
        self.pan_x = 0.0
        self.pan_y = 0.0
        self._dragging = False
        self._drag_x = 0.0
        self._drag_y = 0.0
        self.select_mode = False
        self.selection_start = None
        self.selection_end = None
        self.selection = None
        self.wcs_center = None
        self.rotation_mode = False
        self.rotation_start = None
        self.rotation_end = None
        self.star_layer = []
        self.object_layer = []
        self.star_layer_visible = True
        self.object_layer_visible = True
        self.hover_target = None
        self.pyramid_levels = []
        self.logical_size = None
        self.level_scale = 1.0
        self.set_app_paintable(True)
        self.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK
            | Gdk.EventMask.POINTER_MOTION_MASK
            | Gdk.EventMask.BUTTON_RELEASE_MASK
            | Gdk.EventMask.LEAVE_NOTIFY_MASK
        )
        self.connect("draw", self._on_draw)
        self.connect("leave-notify-event", self._on_leave)
        self.hover_window = Gtk.Window(type=Gtk.WindowType.POPUP)
        self.hover_window.set_type_hint(Gdk.WindowTypeHint.TOOLTIP)
        self.hover_window.set_decorated(False)
        self.hover_window.set_accept_focus(False)
        self.hover_window.set_skip_taskbar_hint(True)
        self.hover_label = Gtk.Label()
        self.hover_label.set_line_wrap(True)
        self.hover_label.set_max_width_chars(42)
        self.hover_window.add(self.hover_label)
        self.hover_window.show_all()
        self.hover_window.hide()

    def load(self, path: str) -> None:
        self.set_pixbuf(GdkPixbuf.Pixbuf.new_from_file(path), path)

    def set_pixbuf(self, pixbuf: GdkPixbuf.Pixbuf, path: str = None) -> None:
        self.pixbuf = pixbuf
        self.path = path
        self.logical_size = (pixbuf.get_width(), pixbuf.get_height())
        self.level_scale = 1.0
        self.pyramid_levels = []
        self.fit = True
        self.zoom = 1.0
        self.star_layer = []
        self.object_layer = []
        self.reset_pan()
        self.queue_draw()

    def set_pyramid(self, levels, full_size=None) -> None:
        self.pyramid_levels = list(levels)
        if full_size is not None:
            self.logical_size = tuple(full_size)
        self._refresh_level()

    def _refresh_level(self) -> None:
        if not self.pyramid_levels or self.logical_size is None:
            return
        width, height = self.logical_size
        allocation = self.get_allocation()
        if self.fit and allocation.width and allocation.height:
            display_scale = min(allocation.width / width, allocation.height / height)
        else:
            display_scale = self.zoom
        level = choose_level(self.pyramid_levels, display_scale)
        if level is None or level[0] == self.path:
            return
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(level[0])
        except GLib.Error:
            return
        self.pixbuf = pixbuf
        self.path = level[0]
        self.level_scale = level[1]
        self.queue_draw()

    def clear(self) -> None:
        self.pixbuf = None
        self.path = None
        self.pyramid_levels = []
        self.logical_size = None
        self.level_scale = 1.0
        self.reset_pan()
        self.queue_draw()

    def reset_pan(self) -> None:
        self.pan_x = 0.0
        self.pan_y = 0.0
        self._dragging = False

    def set_star_layer(self, detections) -> None:
        self.star_layer = list(detections)
        self.queue_draw()

    def set_object_layer(self, objects) -> None:
        self.object_layer = list(objects)
        self.queue_draw()

    def toggle_star_layer(self) -> bool:
        self.star_layer_visible = not self.star_layer_visible
        self.queue_draw()
        return self.star_layer_visible

    def toggle_object_layer(self) -> bool:
        self.object_layer_visible = not self.object_layer_visible
        self.queue_draw()
        return self.object_layer_visible

    def set_rotation_mode(self, enabled: bool) -> None:
        self.rotation_mode = enabled
        self.rotation_start = None
        self.rotation_end = None
        window = self.get_window()
        display = Gdk.Display.get_default()
        if window is not None and display is not None:
            cursor_type = Gdk.CursorType.CROSSHAIR if enabled else Gdk.CursorType.LEFT_PTR
            window.set_cursor(Gdk.Cursor.new_for_display(display, cursor_type))
        if not enabled:
            self.hide_tooltip()
        self.queue_draw()

    def show_tooltip(self, text: str, x: float, y: float) -> None:
        self.hover_label.set_text(text)
        window = self.get_window()
        if window is not None:
            root_x, root_y = window.get_root_coords(int(x), int(y))
            self.hover_window.move(root_x + 16, root_y + 16)
        self.hover_window.show_all()

    def hide_tooltip(self) -> None:
        self.hover_window.hide()

    def _on_leave(self, *_args) -> bool:
        self.hide_tooltip()
        self.set_hover_target(None)
        return False

    def set_hover_target(self, target) -> None:
        if self.hover_target != target:
            self.hover_target = target
            self.queue_draw()

    def _layer_hit(self, x: float, y: float):
        _allocation, scale, offset_x, offset_y = self._view_parameters()
        if scale <= 0:
            return None, None
        if self.star_layer and self.star_layer_visible:
            top_flux = max((star.flux for star in self.star_layer), default=1.0) or 1.0
            for rank, star in enumerate(self.star_layer[:500], start=1):
                sx = offset_x + star.x * scale
                sy = offset_y + star.y * scale
                display_radius = star_display_radius(star.flux, top_flux)
                radius = display_radius + 4
                if (x - sx) ** 2 + (y - sy) ** 2 <= radius ** 2:
                    return (
                        "Star #%d  x=%.1f y=%.1f\n"
                        "flux=%.2f  size=%.0f  HFR=%.2f  ecc=%.2f"
                        % (rank, star.x, star.y, star.flux, star.size, star.hfr, star.eccentricity)
                    ), ("star", rank)
                label_x = sx + display_radius + 3
                label_y = sy - display_radius - 2
                if label_x <= x <= label_x + 14 and label_y - 9 <= y <= label_y + 2:
                    return (
                        "Star #%d rank label  x=%.1f y=%.1f\n"
                        "flux=%.2f  HFR=%.2f  ecc=%.2f"
                        % (rank, star.x, star.y, star.flux, star.hfr, star.eccentricity)
                    ), ("star", rank)
        if self.object_layer and self.object_layer_visible:
            for obj in self.object_layer[:30]:
                sx = offset_x + obj.x * scale
                sy = offset_y + obj.y * scale
                radius = max(5.0, min(50.0, (obj.area ** 0.5) * scale / 2.0)) + 4
                if (x - sx) ** 2 + (y - sy) ** 2 <= radius ** 2:
                    return (
                        "Object #%d: %s  x=%.1f y=%.1f\n"
                        "area=%d px  flux=%.1f  ellipticity=%.2f\n"
                        "C=%.2f A=%.2f S=%.2f  Gini=%.2f  M20=%.2f"
                        % (
                            obj.id, obj.object_type, obj.x, obj.y, obj.area, obj.flux,
                            obj.ellipticity, obj.concentration, obj.asymmetry, obj.smoothness,
                            obj.gini, obj.m20,
                        )
                    ), ("object", obj.id)
        return None, None

    def update_hover(self, x: float, y: float) -> None:
        text, target = self._layer_hit(x, y)
        self.set_hover_target(target)
        if text is None:
            self.hide_tooltip()
        else:
            self.show_tooltip(text, x, y)

    def start_rotation(self, x: float, y: float) -> None:
        self.rotation_start = (x, y)
        self.rotation_end = (x, y)
        self.queue_draw()

    def update_rotation(self, x: float, y: float) -> None:
        if self.rotation_start is None:
            return
        self.rotation_end = (x, y)
        self.queue_draw()

    def segment_angle(self):
        if not self.rotation_start or not self.rotation_end:
            return None
        dx = self.rotation_end[0] - self.rotation_start[0]
        dy = self.rotation_end[1] - self.rotation_start[1]
        if abs(dx) < 1 and abs(dy) < 1:
            return None
        return math.degrees(math.atan2(dy, dx))

    def finish_rotation(self):
        angle = self.segment_angle()
        self.rotation_start = None
        self.rotation_end = None
        self.queue_draw()
        return angle

    def set_select_mode(self, enabled: bool) -> None:
        self.select_mode = enabled
        self.selection_start = None
        self.selection_end = None
        self.selection = None
        self.queue_draw()

    def start_selection(self, x: float, y: float) -> None:
        self.selection_start = (x, y)
        self.selection_end = (x, y)
        self.queue_draw()

    def update_selection(self, x: float, y: float) -> None:
        if self.selection_start is None:
            return
        self.selection_end = (x, y)
        self.selection = selection_rectangle(self.selection_start, self.selection_end)
        self.queue_draw()

    def finish_selection(self):
        if self.selection_start is None:
            return None
        self.selection = selection_rectangle(self.selection_start, self.selection_end)
        self.selection_start = None
        self.selection_end = None
        self.queue_draw()
        return self.selection

    def start_pan(self, x: float, y: float) -> None:
        self._dragging = True
        self._drag_x = x
        self._drag_y = y

    def update_pan(self, x: float, y: float) -> bool:
        if not self._dragging:
            return False
        self.pan_x += x - self._drag_x
        self.pan_y += y - self._drag_y
        self._drag_x = x
        self._drag_y = y
        self.queue_draw()
        return True

    def end_pan(self) -> None:
        self._dragging = False

    def zoom_in(self) -> None:
        self.fit = False
        self.zoom = min(self.zoom * 1.25, 32.0)
        self._refresh_level()
        self.queue_draw()

    def zoom_out(self) -> None:
        self.fit = False
        self.zoom = max(self.zoom / 1.25, 0.05)
        self._refresh_level()
        self.queue_draw()

    def zoom_fit(self) -> None:
        self.fit = True
        self.zoom = 1.0
        self.reset_pan()
        self._refresh_level()
        self.queue_draw()

    def set_zoom_scale(self, scale: float) -> None:
        self.fit = False
        self.zoom = min(max(scale, 0.01), 32.0)
        self._refresh_level()
        self.queue_draw()

    def _view_parameters(self):
        allocation = self.get_allocation()
        if self.pixbuf is None:
            return allocation, 1.0, 0.0, 0.0
        width, height = self.logical_size or (
            self.pixbuf.get_width(), self.pixbuf.get_height()
        )
        if self.fit:
            scale = min(allocation.width / width, allocation.height / height)
        else:
            scale = self.zoom
        offset_x = (allocation.width - width * scale) / 2.0 + self.pan_x
        offset_y = (allocation.height - height * scale) / 2.0 + self.pan_y
        return allocation, scale, offset_x, offset_y

    def selection_at(self, x: float, y: float) -> bool:
        if not self.selection:
            return False
        rx, ry, width, height = self.selection
        return rx <= x <= rx + width and ry <= y <= ry + height

    def image_rectangle(self):
        if not self.selection or self.pixbuf is None:
            return None
        _allocation, scale, offset_x, offset_y = self._view_parameters()
        if scale <= 0:
            return None
        rx, ry, width, height = self.selection
        full_width, full_height = self.logical_size or (
            self.pixbuf.get_width(), self.pixbuf.get_height()
        )
        x = int(max(0, min(full_width - 1, (rx - offset_x) / scale)))
        y = int(max(0, min(full_height - 1, (ry - offset_y) / scale)))
        w = int(max(1, min(full_width - x, width / scale)))
        h = int(max(1, min(full_height - y, height / scale)))
        return x, y, w, h

    def image_coordinates(self, x: float, y: float):
        _, scale, offset_x, offset_y = self._view_parameters()
        if self.pixbuf is None or scale <= 0:
            return None
        column = int((x - offset_x) / scale)
        row = int((y - offset_y) / scale)
        width, height = self.logical_size or (
            self.pixbuf.get_width(), self.pixbuf.get_height()
        )
        if 0 <= column < width and 0 <= row < height:
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
        cr.scale(scale / self.level_scale, scale / self.level_scale)
        Gdk.cairo_set_source_pixbuf(cr, self.pixbuf, 0, 0)
        cr.paint()
        cr.restore()
        if self.star_layer and self.star_layer_visible:
            cr.set_font_size(9)
            top_flux = max((star.flux for star in self.star_layer), default=1.0) or 1.0
            for rank, star in enumerate(self.star_layer[:500], start=1):
                x = offset_x + star.x * scale
                y = offset_y + star.y * scale
                if not (0 <= x <= allocation.width and 0 <= y <= allocation.height):
                    continue
                radius = star_display_radius(star.flux, top_flux)
                highlighted = self.hover_target == ("star", rank)
                alpha = 1.0 if highlighted else 0.35 + star.flux / top_flux * 0.55
                line_width = 2.6 if highlighted else 1.2
                cr.set_source_rgba(1.0, 0.90 if highlighted else 0.80, 0.20, alpha)
                cr.set_line_width(line_width)
                cr.new_path()
                cr.arc(x, y, radius + (1.5 if highlighted else 0), 0, 2 * math.pi)
                cr.stroke()
                label_x = x + radius + 3
                label_y = y - radius - 2
                cr.set_font_size(10 if highlighted else 9)
                cr.set_source_rgba(1.0, 0.95, 0.35, 1.0 if highlighted else 0.85)
                cr.move_to(label_x, label_y)
                cr.show_text(str(rank))
                cr.new_path()
                cr.set_font_size(9)
        if self.object_layer and self.object_layer_visible:
            cr.set_font_size(9)
            for obj in self.object_layer[:30]:
                x = offset_x + obj.x * scale
                y = offset_y + obj.y * scale
                if not (0 <= x <= allocation.width and 0 <= y <= allocation.height):
                    continue
                radius = max(5.0, min(50.0, (obj.area ** 0.5) * scale / 2.0))
                highlighted = self.hover_target == ("object", obj.id)
                cr.set_source_rgba(
                    0.45 if highlighted else 0.30,
                    0.90 if highlighted else 0.70,
                    1.0,
                    1.0 if highlighted else 0.85,
                )
                cr.set_line_width(2.6 if highlighted else 1.4)
                cr.new_path()
                cr.arc(x, y, radius + (2 if highlighted else 0), 0, 2 * math.pi)
                cr.stroke()
                cr.move_to(x + radius + 2, y - radius - 2)
                cr.show_text("%d %s" % (obj.id, obj.object_type))
                cr.new_path()
        rectangle = self.selection
        if self.selection_start is not None and self.selection_end is not None:
            rectangle = selection_rectangle(self.selection_start, self.selection_end)
        if rectangle:
            x, y, width, height = rectangle
            cr.set_source_rgba(0.20, 0.75, 1.0, 0.25)
            cr.rectangle(x, y, width, height)
            cr.fill()
            cr.set_source_rgb(0.20, 0.75, 1.0)
            cr.set_line_width(2)
            cr.rectangle(x, y, width, height)
            cr.stroke()
        if self.rotation_start and self.rotation_end:
            cr.set_source_rgb(1.0, 0.65, 0.2)
            cr.set_line_width(2)
            cr.move_to(*self.rotation_start)
            cr.line_to(*self.rotation_end)
            cr.stroke()
        if self.wcs_center is not None:
            cx = offset_x + self.wcs_center[0] * scale
            cy = offset_y + self.wcs_center[1] * scale
            cr.set_source_rgb(1.0, 0.85, 0.2)
            cr.set_line_width(1.5)
            cr.arc(cx, cy, 12, 0, 2 * math.pi)
            cr.stroke()
            cr.move_to(cx - 18, cy)
            cr.line_to(cx + 18, cy)
            cr.move_to(cx, cy - 18)
            cr.line_to(cx, cy + 18)
            cr.stroke()
        return False

