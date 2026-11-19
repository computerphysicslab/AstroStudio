"""Main GTK window: menus, toolbars, metadata, backend status and log drawer."""

import os
import shutil
import time
from datetime import datetime
from typing import List, Optional

import gi

from .. import BUILD_DATE, __version__

gi.require_version("Gdk", "3.0")
gi.require_version("GdkPixbuf", "2.0")
gi.require_version("Gtk", "3.0")

from gi.repository import Gdk, GdkPixbuf, Gio, GLib, Gtk, Pango  # noqa: E402

from ..adapters import ExifToolAdapter, ImageMagickAdapter, SkyStackerAdapter  # noqa: E402
from ..core import (  # noqa: E402
    EXPORT_FORMATS,
    ExportFormat,
    ImageWorkspace,
    WorkingImage,
    find_output,
    unique_export_path,
    find_plate_solution,
    parse_histogram_text,
    summarize_solution,
)
from .histogram_panel import HistogramWidget  # noqa: E402
from .preview import PreviewPane  # noqa: E402
from .resource_monitor import ResourceMonitor  # noqa: E402

MENU_LAYOUT = (
    (
        "File",
        (
            ("Open", "open"),
            ("Export / Save As", "export"),
            (None, None),
            ("Close", "close"),
            ("Close All", "close-all"),
            (None, None),
            ("Quit", "quit"),
        ),
    ),
    (
        "Edit",
        (
            ("Undo (pipeline state)", "undo"),
            ("Redo (pipeline state)", "redo"),
            (None, None),
            ("Select Area", "select-area"),
            ("Clone Stamp", "clone-stamp"),
        ),
    ),
    (
        "Processing",
        (
            (
                "Precise Scale",
                None,
                (
                    ("10%", "zoom-10"),
                    ("25%", "zoom-25"),
                    ("50%", "zoom-50"),
                    ("75%", "zoom-75"),
                    ("100%", "zoom-100"),
                    ("150%", "zoom-150"),
                    ("200%", "zoom-200"),
                    ("400%", "zoom-400"),
                    ("1000%", "zoom-1000"),
                    (None, None),
                    ("1:1 (pixel per pixel)", "zoom-1-1"),
                    ("Fit to Window", "zoom-fit"),
                ),
            ),
            ("Resize Image...", "resize"),
            ("Calibration", "calibration"),
            ("Stacking", "stacking"),
            ("Image Geometry", "geometry"),
            ("Field Derotator", "derotator"),
        ),
    ),
    (
        "Astrometry",
        (
            ("Plate Solve...", "plate-solve"),
            ("Gaia Sky Map...", "sky-map"),
            ("Survey Cutout...", "survey-cutout"),
        ),
    ),
    (
        "Arithmetic",
        (
            ("Image Combination", "arithmetic"),
            ("Constant Operations", "arithmetic"),
            ("RGB Combination", "arithmetic"),
            ("Split Channels", "arithmetic"),
        ),
    ),
    (
        "Color",
        (
            ("Histogram Manipulation", "color"),
            ("Curves Adjustment", "color"),
            ("Saturation / Balance", "color"),
            ("Gradient Removal", "gradient"),
        ),
    ),
    (
        "Filter",
        (
            (
                "Sharpen",
                None,
                (
                    ("Unsharp Mask (preset)", "unsharp"),
                    ("Sharpen", "filter-sharpen"),
                    ("Convolve Sharpen", "filter-convolve-sharpen"),
                ),
            ),
            (
                "Smooth & Denoise",
                None,
                (
                    ("Blur", "filter-blur"),
                    ("Gaussian Blur", "filter-gaussian-blur"),
                    ("Median", "filter-median"),
                    ("Despeckle", "filter-despeckle"),
                    ("Adaptive Blur", "filter-adaptive-blur"),
                ),
            ),
            (
                "Convolution & Morphology",
                None,
                (
                    ("Convolve Gaussian", "filter-convolve-gaussian"),
                    ("Morphological Erode", "filter-morphology-erode"),
                    ("Edge", "filter-edge"),
                    ("Emboss", "filter-emboss"),
                ),
            ),
            (
                "Astronomical",
                None,
                (
                    ("Star Size Reduction", "filter-star-reduction"),
                    ("Deconvolution", "deconvolution"),
                    ("Background Extraction", "gradient"),
                    ("Asinh Stretch", "filter-stretch"),
                ),
            ),
        ),
    ),
    (
        "View",
        (
            ("Zoom In", "zoom-in"),
            ("Zoom Out", "zoom-out"),
            ("Fit to Window", "zoom-fit"),
            (None, None),
            ("Histogram", "histogram"),
            ("Pixel Line Profile", "line-profile"),
            ("Metadata Viewer", "metadata"),
            ("Toggle Backends Viewer", "toggle-backends"),
            ("Toggle Terminal Drawer", "toggle-terminal"),
        ),
    ),
    (
        "Options",
        (
            ("Backend Settings", "settings"),
            ("Language", "language"),
        ),
    ),
    (
        "Help",
        (
            ("About", "about"),
        ),
    ),
)

IMAGE_EXTENSIONS = (
    "png",
    "jpg",
    "jpeg",
    "tif",
    "tiff",
    "bmp",
    "fits",
    "fit",
    "fts",
    "cr2",
    "cr3",
    "nef",
    "arw",
    "dng",
    "xisf",
)

TOOL_ITEMS = (
    ("edit-undo", "Undo", "undo"),
    ("edit-redo", "Redo", "redo"),
    ("document-open", "Open", "open"),
    ("document-save-as", "Export", "export"),
    ("dialog-information", "Metadata", "metadata"),
    ("zoom-in", "Zoom in", "zoom-in"),
    ("zoom-out", "Zoom out", "zoom-out"),
    ("zoom-fit-best", "Fit to window", "zoom-fit"),
)


def log_segments(line: str):
    """Split a terminal line into (text, tag) pairs for syntax highlighting."""
    segments = []
    if line.startswith("[") and "] " in line:
        end = line.find("] ")
        segments.append((line[: end + 2], "timestamp"))
        line = line[end + 2 :]
    lowered = line.lower()
    if line.startswith("[stderr]") or "failed" in lowered or "error" in lowered:
        segments.append((line, "error"))
    elif line.startswith("CLI ") and ": " in line and " exit " not in line:
        head, arguments = line.split(": ", 1)
        segments.append((head + ": ", "command_label"))
        for token in arguments.split(" "):
            segments.append((token + " ", "argument" if token.startswith("-") else "program"))
    elif line.startswith("CLI ") and " exit " in line:
        segments.append((line, "ok" if "exit 0" in line else "error"))
    else:
        segments.append((line, "response"))
    return segments


TOGGLE_PANELS = {
    "toggle-backends": "Backends Viewer",
    "toggle-terminal": "Terminal Drawer",
}


def toggle_label(action: str, label: str, visible: bool) -> str:
    return "%s: %s" % (label, "On" if visible else "Off")


def append_menu_items(menu: Gio.Menu, items, registry: dict = None) -> None:
    for item in items:
        if item[0] is None:
            menu.append_section(None, Gio.Menu.new())
        elif len(item) == 3:
            child = Gio.Menu.new()
            append_menu_items(child, item[2], registry)
            menu.append_submenu(item[0], child)
        else:
            menu_item = Gio.MenuItem.new(item[0], "app." + item[1])
            menu.append_item(menu_item)
            if registry is not None:
                registry[item[1]] = menu_item


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, app, registry, scratch, engine) -> None:
        super().__init__(application=app, title="Astro Studio")
        self.app = app
        self.settings = app.settings
        self.operation_log = app.operation_log
        self.estimator = app.estimator
        self._progress_timer = None
        self._progress_started = None
        self._progress_estimate = None
        self.registry = registry
        self.scratch = scratch
        self.engine = engine
        self._magick_adapter = ImageMagickAdapter()
        self.adapters = {
            "ImageMagick": self._magick_adapter,
            "ExifTool": ExifToolAdapter(),
            "SkyStacker": SkyStackerAdapter(),
        }
        self.workspace = ImageWorkspace(scratch, engine, self._magick_adapter)
        self.current_images: List[WorkingImage] = []
        self.current_paths = []
        self.export_format: ExportFormat = EXPORT_FORMATS[0]
        self.job_counter = 0
        self.plate_solutions: dict = {}
        self.plate_centers: dict = {}
        self._busy_count = 0
        self.metadata_pending = 0
        self.metadata_window = None
        self.histogram_pending = 0
        self.histogram_datasets = []
        self.histogram_window = None
        self._menu_items: dict = {}
        self._view_menu = None
        gtk_settings = Gtk.Settings.get_default()
        self._system_theme = (
            gtk_settings.get_property("gtk-theme-name") if gtk_settings else "Adwaita",
            bool(
                gtk_settings.get_property("gtk-application-prefer-dark-theme")
                if gtk_settings
                else False
            ),
        )
        self.set_default_size(1100, 720)

        self.preview = PreviewPane()
        self.preview.set_size_request(640, 480)
        self.preview.add_events(Gdk.EventMask.SCROLL_MASK)
        self.preview.connect("button-press-event", self._on_canvas_click)
        self.preview.connect("motion-notify-event", self._on_canvas_motion)
        self.preview.connect("button-release-event", self._on_canvas_release)
        self.preview.connect("scroll-event", self._on_preview_scroll)

        self._build_layout()
        self._apply_theme()
        self.connect("destroy", lambda *_widget: self.resource_monitor.stop())
        self.on_backends_updated(registry)

    def _build_layout(self) -> None:
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(root)

        self.menu_bar = self._build_menu_bar()
        root.pack_start(self.menu_bar, False, False, 0)
        root.pack_start(self._build_toolbar(), False, False, 0)

        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned.set_position(740)

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        frame = Gtk.Frame(label="Preview (PNG rendered from TIFF)")
        self.preview_scroll = Gtk.ScrolledWindow()
        self.preview_scroll.add(self.preview)
        frame.add(self.preview_scroll)
        left.pack_start(frame, True, True, 0)
        paned.pack1(left, True, False)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        right.set_border_width(6)
        self.resource_monitor = ResourceMonitor()
        right.pack_start(self.resource_monitor, False, False, 0)
        self.backends_panel = self._panel_with_close(
            "Backends (startup discovery)", self._build_backend_content()
        )
        self.metadata_panel = self._panel_with_close(
            "Metadata (ExifTool, read-only)", self._build_metadata_content()
        )
        self.metadata_panel.set_no_show_all(True)
        self.terminal_panel = self._panel_with_close(
            "Terminal Drawer", self._build_log_content()
        )
        right.pack_start(self.backends_panel, False, False, 0)
        right.pack_start(self.metadata_panel, False, False, 0)
        right.pack_start(self.terminal_panel, True, True, 0)
        paned.pack2(right, False, True)
        root.pack_start(paned, True, True, 0)

        self.status_bar = Gtk.Statusbar()
        self.status_context = self.status_bar.get_context_id("astro-studio")
        self._status("Astro Studio ready")
        root.pack_start(self.status_bar, False, False, 0)
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_size_request(-1, 8)
        root.pack_start(self.progress_bar, False, False, 0)
        self._rebuild_menu_bar()

    def _dynamic_entries(self, entries):
        result = []
        for item in entries:
            if item[0] is None:
                result.append(item)
            elif len(item) == 3:
                result.append((item[0], None, self._dynamic_entries(item[2])))
            elif item[1] in TOGGLE_PANELS:
                panel = getattr(
                    self,
                    "backends_panel"
                    if item[1] == "toggle-backends"
                    else "terminal_panel",
                    None,
                )
                visible = panel.get_visible() if panel is not None else True
                result.append(
                    (toggle_label(item[1], TOGGLE_PANELS[item[1]], visible), item[1])
                )
            else:
                result.append(item)
        return result

    def _build_menu_bar(self) -> Gtk.Widget:
        menu = Gio.Menu.new()
        for label, entries in MENU_LAYOUT:
            submenu = Gio.Menu.new()
            append_menu_items(submenu, self._dynamic_entries(entries), self._menu_items)
            menu.append_submenu(label, submenu)
        return Gtk.MenuBar.new_from_model(menu)

    def _rebuild_menu_bar(self) -> None:
        root = self.get_child()
        if root is None or self.menu_bar is None:
            return
        root.remove(self.menu_bar)
        self.menu_bar = self._build_menu_bar()
        root.pack_start(self.menu_bar, False, False, 0)
        root.reorder_child(self.menu_bar, 0)
        self.menu_bar.show_all()

    def _build_toolbar(self) -> Gtk.Widget:
        toolbar = Gtk.Toolbar()
        for icon, label, action in TOOL_ITEMS:
            button = Gtk.ToolButton.new(
                Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.BUTTON), label
            )
            button.set_tooltip_text(label)
            button.connect("clicked", lambda *_widget, name=action: self._activate(name))
            toolbar.insert(button, -1)
        return toolbar

    def _panel_with_close(self, title: str, content: Gtk.Widget) -> Gtk.Widget:
        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        label = Gtk.Label(label=title, xalign=0.0)
        label.set_hexpand(True)
        close_button = Gtk.Button.new_from_icon_name(
            "window-close-symbolic", Gtk.IconSize.MENU
        )
        close_button.set_tooltip_text("Close panel")
        close_button.connect("clicked", lambda *_: self._on_panel_closed(panel))
        header.pack_start(label, True, True, 0)
        header.pack_start(close_button, False, False, 0)
        panel.pack_start(header, False, False, 0)
        panel.pack_start(content, True, True, 0)
        return panel

    def _build_backend_content(self) -> Gtk.Widget:
        self.backend_store = Gtk.ListStore(str, str, str)
        view = Gtk.TreeView(model=self.backend_store)
        for index, title in enumerate(("Name", "Status", "Version")):
            view.append_column(
                Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=index)
            )
        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(130)
        scroll.add(view)
        return scroll

    def _build_metadata_content(self) -> Gtk.Widget:
        notebook = Gtk.Notebook()
        self.metadata_buffers = {}
        for label, key in (
            ("PNG preview", "png"),
            ("TIFF working", "tiff"),
        ):
            buffer = Gtk.TextBuffer()
            buffer.set_text("Press the (i) Metadata button to read ExifTool tags.")
            view = Gtk.TextView(buffer=buffer)
            view.set_editable(False)
            view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
            view.override_font(Pango.FontDescription("monospace 10"))
            scroll = Gtk.ScrolledWindow()
            scroll.set_min_content_width(360)
            scroll.set_min_content_height(140)
            scroll.add(view)
            notebook.append_page(scroll, Gtk.Label(label=label))
            self.metadata_buffers[key] = buffer
        return notebook

    def _build_log_content(self) -> Gtk.Widget:
        self.log_buffer = Gtk.TextBuffer()
        for name, properties in (
            ("timestamp", {"foreground": "#7f8c8d"}),
            ("command_label", {"foreground": "#5dade2", "weight": Pango.Weight.BOLD}),
            ("program", {"foreground": "#9b59b6", "weight": Pango.Weight.BOLD}),
            ("argument", {"foreground": "#f1c40f"}),
            ("response", {"foreground": "#d5d8dc"}),
            ("ok", {"foreground": "#2ecc71", "weight": Pango.Weight.BOLD}),
            ("error", {"foreground": "#ff6b6b", "weight": Pango.Weight.BOLD}),
        ):
            self.log_buffer.create_tag(name, **properties)
        self.log_view = Gtk.TextView(buffer=self.log_buffer)
        self.log_view.set_editable(False)
        self.log_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self.log_view.override_font(Pango.FontDescription("monospace 8"))
        scroll = Gtk.ScrolledWindow()
        scroll.add(self.log_view)
        return scroll

    def _apply_theme(self) -> None:
        gtk_settings = Gtk.Settings.get_default()
        if gtk_settings is None:
            return
        choice = self.settings.get("theme", "system")
        if choice == "system":
            name, dark = self._system_theme
        elif choice == "dark":
            name, dark = ("Yaru-dark", True)
            if not os.path.isdir("/usr/share/themes/Yaru-dark"):
                name = "Adwaita-dark"
        else:
            name, dark = ("Yaru-light", False)
            if not os.path.isdir("/usr/share/themes/Yaru-light"):
                name = "Adwaita"
        gtk_settings.set_property("gtk-theme-name", name)
        gtk_settings.set_property("gtk-application-prefer-dark-theme", dark)

    def _update_toggle_labels(self) -> None:
        self._rebuild_menu_bar()

    def _activate(self, action: str) -> None:
        gio_action = self.app.lookup_action(action)
        if gio_action is not None and not gio_action.get_enabled():
            self._log("Action unavailable: %s (check Backends panel)" % action)
            self._status("Action unavailable: %s" % action)
            return
        self.app.activate_action(action, None)

    def _status(self, text: str) -> None:
        self.status_bar.push(self.status_context, text)

    @staticmethod
    def _megapixels(path: str) -> float:
        try:
            _format, width, height = GdkPixbuf.Pixbuf.get_file_info(path)
            return width * height / 1_000_000.0
        except (TypeError, ValueError):
            return 1.0

    def _current_megapixels(self) -> float:
        if self.preview.pixbuf is not None:
            return (
                self.preview.pixbuf.get_width() * self.preview.pixbuf.get_height()
            ) / 1_000_000.0
        if self.current_paths:
            return self._megapixels(self.current_paths[-1])
        return 1.0

    def _begin_estimate(self, stage: str, megapixels: float, message: str) -> None:
        seconds = self.estimator.estimate(stage, megapixels)
        if seconds is None:
            self._status(message)
            return
        self._status("%s (est. %.1f s)" % (message, seconds))
        self._stop_progress()
        self._progress_started = time.monotonic()
        self._progress_estimate = seconds
        self.progress_bar.set_fraction(0.0)
        self._progress_timer = GLib.timeout_add(100, self._tick_progress)

    def _tick_progress(self) -> bool:
        if self._progress_started is None or not self._progress_estimate:
            return False
        elapsed = time.monotonic() - self._progress_started
        self.progress_bar.set_fraction(min(1.0, elapsed / self._progress_estimate))
        return True

    def _stop_progress(self) -> None:
        if self._progress_timer is not None:
            GLib.source_remove(self._progress_timer)
            self._progress_timer = None
        self._progress_started = None
        self._progress_estimate = None
        self.progress_bar.set_fraction(0.0)

    def _status_image(self, image: WorkingImage, message: str) -> None:
        try:
            png_mb = os.path.getsize(image.png_path) / (1024.0 * 1024.0)
            tiff_mb = os.path.getsize(image.tiff_path) / (1024.0 * 1024.0)
            self._status(
                "%s | PNG %.2f MB | TIFF %.2f MB" % (message, png_mb, tiff_mb)
            )
        except OSError:
            self._status(message)

    def _busy_begin(self) -> None:
        self._busy_count += 1
        if self._busy_count == 1:
            window = self.get_window()
            if window is not None:
                display = Gdk.Display.get_default()
                cursor = (
                    Gdk.Cursor.new_from_name(display, "watch") if display else None
                )
                if cursor is not None:
                    window.set_cursor(cursor)

    def _busy_end(self) -> None:
        self._busy_count = max(0, self._busy_count - 1)
        if self._busy_count == 0:
            window = self.get_window()
            if window is not None:
                window.set_cursor(None)

    def _log(self, line: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        segments = log_segments("[%s] %s" % (timestamp, line))
        for index, (text, tag) in enumerate(segments):
            suffix = "\n" if index == len(segments) - 1 else ""
            self.log_buffer.insert_with_tags_by_name(
                self.log_buffer.get_end_iter(), text + suffix, tag
            )
        self.log_view.scroll_to_iter(self.log_buffer.get_end_iter(), 0.0, False, 0.0, 0.0)

    def _capture_view_state(self) -> dict:
        return {
            "zoom": self.preview.zoom,
            "fit": self.preview.fit,
            "pan_x": self.preview.pan_x,
            "pan_y": self.preview.pan_y,
            "x": self.preview_scroll.get_hadjustment().get_value(),
            "y": self.preview_scroll.get_vadjustment().get_value(),
        }

    def _restore_view_state(self, state: dict) -> None:
        if state is None:
            return
        if state["fit"]:
            self.preview.zoom_fit()
        else:
            self.preview.set_zoom_scale(state["zoom"])
        self.preview.pan_x = state["pan_x"]
        self.preview.pan_y = state["pan_y"]
        self.preview.queue_draw()
        self.preview_scroll.get_hadjustment().set_value(state["x"])
        self.preview_scroll.get_vadjustment().set_value(state["y"])

    def _show_error(self, message: str) -> None:
        dialog = Gtk.MessageDialog(
            parent=self,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=message,
        )
        dialog.run()
        dialog.destroy()

    def _on_canvas_click(self, widget, event) -> bool:
        button = event.button
        if not isinstance(button, int):
            button = button.button
        if event.type == Gdk.EventType.DOUBLE_BUTTON_PRESS and button == 1:
            self.action_zoom_fit()
            return True
        position = self.preview.image_coordinates(event.x, event.y)
        if position:
            self._status("X=%d  Y=%d (drag to pan)" % position)
        if button == 1:
            self.preview.start_pan(event.x, event.y)
        return True

    def _on_canvas_motion(self, widget, event) -> bool:
        return self.preview.update_pan(event.x, event.y)

    def _on_canvas_release(self, widget, event) -> bool:
        self.preview.end_pan()
        return False

    def _on_preview_scroll(self, widget, event) -> bool:
        if event.direction == Gdk.ScrollDirection.UP:
            self.preview.zoom_in()
        elif event.direction == Gdk.ScrollDirection.DOWN:
            self.preview.zoom_out()
        else:
            return False
        zoom = "fit" if self.preview.fit else "%.0f%%" % (self.preview.zoom * 100)
        self._status("Zoom: %s (mouse wheel)" % zoom)
        return True

    def on_backends_updated(self, registry) -> None:
        self.backend_store.clear()
        statuses = sorted(
            registry.status.values(),
            key=lambda status: (not status.available, status.name.lower()),
        )
        for status in statuses:
            self.backend_store.append(status.label())
        available = sum(1 for status in registry.status.values() if status.available)
        self._status(
            "%d/%d backends installed | %d image(s) open"
            % (available, len(registry.status), len(self.current_paths))
        )
        self.app.update_action_sensitivity()
        self._update_toggle_labels()

    def action_open(self) -> None:
        dialog = Gtk.FileChooserDialog(
            title="Open images",
            parent=self,
            action=Gtk.FileChooserAction.OPEN,
            buttons=(
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OPEN,
                Gtk.ResponseType.OK,
            ),
        )
        dialog.set_select_multiple(True)
        image_filter = Gtk.FileFilter()
        image_filter.set_name("Images (PNG, JPEG, TIFF, FITS, BMP, RAW)")
        for extension in IMAGE_EXTENSIONS:
            image_filter.add_pattern("*." + extension)
            image_filter.add_pattern("*." + extension.upper())
        all_filter = Gtk.FileFilter()
        all_filter.set_name("All files")
        all_filter.add_pattern("*")
        dialog.add_filter(image_filter)
        dialog.add_filter(all_filter)
        dialog.set_filter(image_filter)
        if dialog.run() == Gtk.ResponseType.OK:
            for path in dialog.get_filenames():
                self._open_file(path)
        dialog.destroy()

    def _open_file(self, path: str) -> None:
        if not self.registry.available("ImageMagick"):
            self._log("Backend unavailable: ImageMagick is required for the TIFF workspace")
            return
        self.current_paths.append(path)
        self.operation_log.record("open_requested", source=path)
        self._busy_begin()
        image = self.workspace.prepare(
            path,
            on_ready=self._on_image_ready,
            on_error=self._on_workspace_error,
            on_log=self._log,
        )
        self.current_images.append(image)
        self._begin_estimate(
            "open", self._megapixels(path), "Preparing TIFF + PNG for %s" % path
        )

    def _on_image_ready(self, image: WorkingImage) -> None:
        self._busy_end()
        self._stop_progress()
        self.preview.load(image.png_path)
        self._status_image(image, "Ready: %s" % os.path.basename(image.source))
        self._log(
            "Workspace ready: TIFF=%s | PNG=%s"
            % (image.tiff_path, image.png_path)
        )

    def _on_workspace_error(self, message: str) -> None:
        self._busy_end()
        self._stop_progress()
        self._status("Workspace error")
        self._log(message)
        self._show_error(message)

    def action_export(self) -> None:
        if not self.current_images:
            self._log("Open an image before exporting")
            self._status("Open an image before exporting")
            return
        selected_format = self._choose_export_format()
        if selected_format is None:
            self._log("Export cancelled: no format selected")
            return
        self.export_format = selected_format
        if selected_format.key != "png8" and not self.registry.available("ImageMagick"):
            self._show_error("ImageMagick is not installed; only PNG export is available.")
            return

        image = self.current_images[-1]
        dialog = Gtk.FileChooserDialog(
            title="Export result",
            parent=self,
            action=Gtk.FileChooserAction.SAVE,
            buttons=(
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_SAVE,
                Gtk.ResponseType.OK,
            ),
        )
        dialog.set_do_overwrite_confirmation(True)
        dialog.set_current_name(
            "%s.%s"
            % (
                os.path.splitext(os.path.basename(image.source))[0],
                selected_format.extension,
            )
        )
        response = dialog.run()
        destination = dialog.get_filename() if response == Gtk.ResponseType.OK else None
        dialog.destroy()
        if not destination:
            self._log("Export cancelled")
            return
        root, extension = os.path.splitext(destination)
        if extension.lower() != "." + selected_format.extension:
            root = destination
            self._log("Extension adjusted to %s" % selected_format.extension)
        directory = os.path.dirname(root) or "."
        stem = os.path.basename(root)
        destination = unique_export_path(directory, stem, selected_format.extension)
        if destination != os.path.join(directory, stem + "." + selected_format.extension):
            self._log("Destination existed; using %s" % os.path.basename(destination))

        self.operation_log.record(
            "export_requested",
            source=image.source,
            destination=destination,
            format=selected_format.key,
        )
        started = time.monotonic()
        self._busy_begin()
        self._begin_estimate(
            "export-" + selected_format.extension,
            self._current_megapixels(),
            "Exporting as %s..." % selected_format.label,
        )
        self.workspace.export(
            image,
            destination,
            on_ready=lambda path: self._on_export_ready(path, started),
            on_error=self._on_workspace_error,
            on_log=self._log,
            export_format=selected_format,
        )
        self.app.update_action_sensitivity()

    def _on_export_ready(self, destination: str, started: float) -> None:
        self._busy_end()
        self._stop_progress()
        size_mb = os.path.getsize(destination) / (1024.0 * 1024.0)
        elapsed = time.monotonic() - started
        self._log("Exported copy to %s" % destination)
        self._status(
            "Export complete: %s (%.2f MB, %.1f s)"
            % (os.path.basename(destination), size_mb, elapsed)
        )
        self.app.update_action_sensitivity()

    def _run_transform(self, params: dict, description: str) -> None:
        if not self.current_images:
            self._log("Open an image before applying a transformation")
            self._status("Open an image first")
            return
        if not self.registry.available("ImageMagick"):
            self._log("Backend unavailable: ImageMagick is required for transformations")
            return
        image = self.current_images[-1]
        view_state = self._capture_view_state()
        started = time.monotonic()
        self._busy_begin()
        stage = next(iter(params), "transform")
        self._begin_estimate(stage, self._current_megapixels(), "%s via CLI..." % description)
        self.workspace.transform(
            image,
            params,
            on_ready=lambda final: self._on_transform_done(final, view_state, started),
            on_error=self._on_workspace_error,
            on_log=self._log,
        )
        self.app.update_action_sensitivity()

    def _on_transform_done(
        self, image: WorkingImage, view_state: dict = None, started: float = None
    ) -> None:
        self._busy_end()
        self._stop_progress()
        self.preview.load(image.png_path)
        self._restore_view_state(view_state)
        self._log("TIFF transformed; preview PNG regenerated: %s" % image.png_path)
        elapsed = time.monotonic() - started if started is not None else 0.0
        self._status_image(
            image, "Transform applied in %.1f s (view unchanged)" % elapsed
        )
        self.app.update_action_sensitivity()

    def _ask_percentage(self) -> Optional[str]:
        dialog = Gtk.Dialog(
            title="Resize image",
            parent=self,
            modal=True,
            buttons=(
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK,
                Gtk.ResponseType.OK,
            ),
        )
        entry = Gtk.Entry()
        entry.set_text("50")
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        box.pack_start(Gtk.Label(label="Scale (%)"), False, False, 0)
        box.pack_start(entry, True, True, 0)
        dialog.get_content_area().pack_start(box, True, True, 6)
        dialog.show_all()
        value = None
        if dialog.run() == Gtk.ResponseType.OK:
            text = entry.get_text().strip().rstrip("%")
            try:
                number = float(text)
            except ValueError:
                number = 0.0
            if 0 < number <= 10000:
                value = "%g%%" % number
            else:
                self._log("Invalid scale; enter a percentage between 0 and 10000")
        dialog.destroy()
        return value

    def action_resize(self) -> None:
        scale = self._ask_percentage()
        if scale:
            self._run_transform({"resize": scale}, "Resize to " + scale)

    def _ask_unsharp(self) -> Optional[str]:
        presets = (
            ("Light", "0.8x1+0.5+0.02"),
            ("Medium", "1.5x1+0.7+0.02"),
            ("Strong", "2.5x1+1.0+0.03"),
        )
        dialog = Gtk.Dialog(
            title="Sharpen image",
            parent=self,
            modal=True,
            buttons=(
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK,
                Gtk.ResponseType.OK,
            ),
        )
        combo = Gtk.ComboBoxText()
        for label, _value in presets:
            combo.append_text(label)
        combo.set_active(1)
        dialog.get_content_area().pack_start(combo, True, True, 6)
        dialog.show_all()
        value = None
        if dialog.run() == Gtk.ResponseType.OK:
            index = combo.get_active()
            if 0 <= index < len(presets):
                value = presets[index][1]
        dialog.destroy()
        return value

    def action_unsharp(self) -> None:
        value = self._ask_unsharp()
        if value:
            self._run_transform({"unsharp": value}, "Sharpen")

    def _run_filter(self, params: dict, label: str) -> None:
        self._run_transform(params, label)

    def action_filter_sharpen(self) -> None:
        self._run_filter({"sharpen": "0x1"}, "Sharpen filter")

    def action_filter_convolve_sharpen(self) -> None:
        kernel = "0,-1,0,-1,5,-1,0,-1,0"
        self._run_filter({"convolve": kernel}, "Convolve sharpen")

    def action_filter_blur(self) -> None:
        self._run_filter({"blur": "0x2"}, "Blur filter")

    def action_filter_gaussian_blur(self) -> None:
        self._run_filter({"gaussian-blur": "0x1.5"}, "Gaussian blur")

    def action_filter_median(self) -> None:
        self._run_filter({"median": "3"}, "Median filter")

    def action_filter_despeckle(self) -> None:
        self._run_filter({"despeckle": True}, "Despeckle")

    def action_filter_adaptive_blur(self) -> None:
        self._run_filter({"adaptive-blur": "0x2"}, "Adaptive blur")

    def action_filter_convolve_gaussian(self) -> None:
        kernel = "1,2,1,2,4,2,1,2,1"
        self._run_filter({"convolve": kernel}, "Convolve gaussian")

    def action_filter_morphology_erode(self) -> None:
        self._run_filter({"morphology": "Erode Disk:1"}, "Morphological erode")

    def action_filter_edge(self) -> None:
        self._run_filter({"edge": "1"}, "Edge filter")

    def action_filter_emboss(self) -> None:
        self._run_filter({"emboss": "1"}, "Emboss filter")

    def action_filter_star_reduction(self) -> None:
        self._run_filter({"morphology": "Erode Disk:1"}, "Star size reduction")

    def _choose_export_format(self) -> Optional[ExportFormat]:
        dialog = Gtk.Dialog(
            title="Choose export format",
            parent=self,
            modal=True,
            buttons=(
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK,
                Gtk.ResponseType.OK,
            ),
        )
        store = Gtk.ListStore(str, str, str)
        for export_format in EXPORT_FORMATS:
            store.append((export_format.key, export_format.label, export_format.category))
        view = Gtk.TreeView(model=store)
        view.append_column(Gtk.TreeViewColumn("Format", Gtk.CellRendererText(), text=1))
        view.append_column(Gtk.TreeViewColumn("Type", Gtk.CellRendererText(), text=2))
        view.connect("row-activated", lambda *_: dialog.response(Gtk.ResponseType.OK))
        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_width(460)
        scroll.set_min_content_height(260)
        scroll.add(view)
        content = dialog.get_content_area()
        content.pack_start(scroll, True, True, 6)
        dialog.show_all()
        for row in store:
            if row[0] == self.export_format.key:
                view.get_selection().select_iter(row.iter)
                break
        selected = None
        if dialog.run() == Gtk.ResponseType.OK:
            selection = view.get_selection().get_selected()[1]
            if selection is not None:
                selected = next(
                    item for item in EXPORT_FORMATS if item.key == store[selection][0]
                )
        dialog.destroy()
        return selected

    def action_metadata(self) -> None:
        if not self.current_images or not self.current_paths:
            self._log("Open an image before reading metadata")
            self._status("Open an image first")
            return
        image = self.current_images[-1]
        self.metadata_pending = 2
        self._read_metadata(self.current_paths[-1], "png", "PNG preview")
        self._read_metadata(image.tiff_path, "tiff", "TIFF working")

    def _read_metadata(self, path: str, buffer_key: str, label: str) -> None:
        adapter = self.adapters["ExifTool"]
        if not self.registry.available(adapter.name):
            self.metadata_buffers[buffer_key].set_text(
                "ExifTool is not installed; metadata is unavailable."
            )
            self._log("CLI unavailable: %s" % adapter.name)
            self._metadata_job_finished()
            return
        self.job_counter += 1
        job_id = "metadata-%d" % self.job_counter
        argv = adapter.build_argv([path])
        self._log("CLI %s (%s): %s" % (job_id, label, " ".join(argv)))
        self._busy_begin()
        self.engine.run(
            job_id,
            argv,
            on_done=lambda result: self._on_metadata_done(result, buffer_key, label),
        )
        self.app.update_action_sensitivity()

    def _on_metadata_done(self, result, buffer_key: str, label: str) -> None:
        self._busy_end()
        if result.ok:
            text = result.stdout.strip() or "(no metadata tags found)"
            self.metadata_buffers[buffer_key].set_text(text)
            self._log(
                "CLI %s exit %d (%s): %d lines"
                % (result.job_id, result.exit_code, label, len(text.splitlines()))
            )
            self._status("Metadata loaded: %s" % label)
        else:
            message = result.error or result.stderr or "unknown error"
            self.metadata_buffers[buffer_key].set_text("Metadata error: %s" % message)
            self._log("CLI %s failed: %s" % (result.job_id, message))
        self._metadata_job_finished()

    def _metadata_job_finished(self) -> None:
        self.metadata_pending = max(0, self.metadata_pending - 1)
        self.app.update_action_sensitivity()
        if self.metadata_pending == 0:
            self._show_metadata_window()

    def _show_metadata_window(self) -> None:
        if self.metadata_window is not None:
            self.metadata_window.destroy()
        window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        window.set_title("Metadata - Astro Studio")
        window.set_transient_for(self)
        window.set_modal(False)
        window.set_default_size(760, 560)
        header = Gtk.HeaderBar()
        header.set_show_close_button(False)
        header.set_title("Metadata (ExifTool, literal output)")
        close_button = Gtk.Button.new_from_icon_name(
            "window-close-symbolic", Gtk.IconSize.BUTTON
        )
        close_button.set_tooltip_text("Close metadata window")
        close_button.connect("clicked", lambda *_: window.destroy())
        header.pack_end(close_button)
        window.set_titlebar(header)

        notebook = Gtk.Notebook()
        for label, title in (("png", "PNG preview"), ("tiff", "TIFF working")):
            view = Gtk.TextView(buffer=self.metadata_buffers[label])
            view.set_editable(False)
            view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
            view.override_font(Pango.FontDescription("monospace 10"))
            scroll = Gtk.ScrolledWindow()
            scroll.add(view)
            notebook.append_page(scroll, Gtk.Label(label=title))
        window.add(notebook)
        window.connect("destroy", self._on_metadata_window_destroyed)
        self.metadata_window = window
        window.show_all()

    def _on_metadata_window_destroyed(self, _widget) -> None:
        self.metadata_window = None

    def action_histogram(self) -> None:
        if not self.current_images:
            self._log("Open an image before requesting a histogram")
            self._status("Open an image first")
            return
        if not self.registry.available("ImageMagick"):
            self._show_error("ImageMagick is not installed; histograms are unavailable.")
            return
        image = self.current_images[-1]
        self.histogram_pending = 2
        self.histogram_datasets = []
        self._busy_begin()
        self._status("Computing histograms via external CLI...")
        for key, path, label, colour in (
            ("preview", image.png_path, "Displayed PNG", (0.30, 0.65, 1.0)),
            ("working", image.tiff_path, "Working TIFF", (0.35, 0.85, 0.45)),
        ):
            argv = [self._magick_adapter.binary, path, "-format", "%c", "histogram:info:-"]
            self._log("CLI histogram-%s: %s" % (key, " ".join(argv)))
            self.job_counter += 1
            job_id = "histogram-%s-%d" % (key, self.job_counter)
            self.engine.run(
                job_id,
                argv,
                on_done=lambda result, k=key, p=path, l=label, c=colour: self._on_histogram_done(
                    result, k, p, l, c
                ),
            )

    def _on_histogram_done(self, result, key: str, path: str, label: str, colour) -> None:
        if result.ok:
            points = parse_histogram_text(result.stdout)
            self.histogram_datasets.append((label, colour, points))
            self._log("CLI %s exit %d (%d bins)" % (result.job_id, result.exit_code, len(points)))
        else:
            self._log("CLI %s failed: %s" % (result.job_id, result.error or result.stderr))
        self.histogram_pending -= 1
        if self.histogram_pending == 0:
            self._busy_end()
            self._show_histogram_window()

    def _show_histogram_window(self) -> None:
        if self.histogram_window is not None:
            self.histogram_window.destroy()
        window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        window.set_title("Histogram - Astro Studio")
        window.set_transient_for(self)
        window.set_default_size(720, 360)
        header = Gtk.HeaderBar()
        header.set_show_close_button(False)
        header.set_title("Histogram (CLI data, logarithmic count axis)")
        close_button = Gtk.Button.new_from_icon_name(
            "window-close-symbolic", Gtk.IconSize.BUTTON
        )
        close_button.set_tooltip_text("Close histogram window")
        close_button.connect("clicked", lambda *_: window.destroy())
        header.pack_end(close_button)
        window.set_titlebar(header)
        chart = HistogramWidget()
        chart.set_datasets(self.histogram_datasets)
        window.add(chart)
        window.connect("destroy", self._on_histogram_window_destroyed)
        self.histogram_window = window
        window.show_all()

    def _on_histogram_window_destroyed(self, _widget) -> None:
        self.histogram_window = None

    def _on_panel_closed(self, panel) -> None:
        panel.hide()
        self._update_toggle_labels()

    def action_toggle_backends(self) -> None:
        if self.backends_panel.get_visible():
            self.backends_panel.hide()
        else:
            self.backends_panel.show()
        self._update_toggle_labels()

    def action_toggle_terminal(self) -> None:
        if self.terminal_panel.get_visible():
            self.terminal_panel.hide()
        else:
            self.terminal_panel.show()
            self.log_view.scroll_to_iter(self.log_buffer.get_end_iter(), 0.0, False, 0.0, 0.0)
        self._update_toggle_labels()

    def action_close(self) -> None:
        if self.current_paths:
            self.current_paths.pop()
        if self.current_images:
            self.current_images.pop()
        self.preview.clear()
        self._status("Closed active view")

    def action_close_all(self) -> None:
        self.current_paths.clear()
        self.current_images.clear()
        self.preview.clear()
        self._status("All views closed")

    def _show_info(self, title: str, text: str) -> None:
        dialog = Gtk.MessageDialog(
            parent=self,
            modal=True,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=title,
        )
        dialog.format_secondary_text(text[:4000])
        dialog.run()
        dialog.destroy()

    def _show_image(self, title: str, path: str) -> None:
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)
        except Exception:
            self._show_info(title, path)
            return
        dialog = Gtk.Dialog(title=title, parent=self, modal=True)
        dialog.add_button(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)
        image = Gtk.Image.new_from_pixbuf(pixbuf)
        dialog.get_content_area().pack_start(image, True, True, 6)
        dialog.show_all()
        dialog.run()
        dialog.destroy()

    def _ask_plate_center(self) -> Optional[str]:
        dialog = Gtk.Dialog(
            title="Plate solving seed (optional)",
            parent=self,
            modal=True,
            buttons=(
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK,
                Gtk.ResponseType.OK,
            ),
        )
        ra_entry = Gtk.Entry()
        dec_entry = Gtk.Entry()
        ra_entry.set_placeholder_text("RA degrees (e.g. 83.82)")
        dec_entry.set_placeholder_text("Dec degrees (e.g. -5.39)")
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.pack_start(Gtk.Label(label="Leave blank for FITS header seed / blind search"), False, False, 0)
        box.pack_start(ra_entry, True, True, 0)
        box.pack_start(dec_entry, True, True, 0)
        dialog.get_content_area().pack_start(box, True, True, 6)
        dialog.show_all()
        center = None
        if dialog.run() == Gtk.ResponseType.OK:
            ra_text = ra_entry.get_text().strip()
            dec_text = dec_entry.get_text().strip()
            if ra_text or dec_text:
                try:
                    float(ra_text)
                    float(dec_text)
                    center = "%s,%s" % (ra_text, dec_text)
                except ValueError:
                    self._show_error("RA and Dec must be decimal degrees")
        dialog.destroy()
        return center

    def _run_astrometry(self, job_name: str, argv: List[str], output_dir: str, on_done) -> None:
        self.job_counter += 1
        job_id = "%s-%d" % (job_name, self.job_counter)
        self._log("CLI %s: %s" % (job_id, " ".join(argv)))
        self._busy_begin()
        self._status("Running %s via SkyStacker..." % job_name)
        self.engine.run(job_id, argv, on_log=self._log, on_done=on_done)
        self.app.update_action_sensitivity()

    def _astrometry_job_dir(self, name: str):
        self.job_counter += 1
        return self.scratch.job_dir("%s-%d" % (name, self.job_counter))

    def _reuse_plate_solution(self, source: str, output_dir: str) -> None:
        solution = self.plate_solutions.get(source)
        if not solution or not os.path.isfile(solution):
            return
        target = os.path.join(output_dir, "plate_solution.json")
        if os.path.abspath(solution) == os.path.abspath(target):
            return
        try:
            shutil.copyfile(solution, target)
            self._log("Reused plate solution: %s -> %s" % (solution, target))
        except OSError as exc:
            self._log("Cannot reuse plate solution: %s" % exc)

    def action_plate_solve(self) -> None:
        if not self.current_paths:
            self._log("Open an image before plate solving")
            return
        if not self.registry.available("SkyStacker"):
            self._show_error("SkyStacker is not installed; plate solving is unavailable.")
            return
        center = self._ask_plate_center()
        source = self.current_paths[-1]
        self.plate_centers[source] = center
        output_dir = self._astrometry_job_dir("plate-solve")
        adapter = self.adapters["SkyStacker"]
        argv = adapter.build_plate_solve_argv(source, output_dir, center)
        self._run_astrometry(
            "plate-solve",
            argv,
            output_dir,
            lambda result: self._on_plate_solve_done(result, output_dir),
        )

    def _on_plate_solve_done(self, result, output_dir: str) -> None:
        self._busy_end()
        if not result.ok:
            self._log("CLI %s failed: %s" % (result.job_id, result.error or result.stderr))
            self._show_error("Plate solving failed: %s" % (result.error or result.stderr))
        else:
            solution = find_plate_solution(output_dir)
            if solution:
                canonical = os.path.join(output_dir, "plate_solution.json")
                if os.path.abspath(solution) != os.path.abspath(canonical):
                    shutil.copyfile(solution, canonical)
                    solution = canonical
                self.plate_solutions[self.current_paths[-1]] = solution
            text = summarize_solution(solution) if solution else "No plate solution was written (check star field and seed)."
            if not any(word in text.lower() for word in ("fov", "ra", "dec", "scale")):
                text = "No field-of-view solution in the report (the field may lack stars):\n" + text
            self._log("CLI %s exit %d; solution: %s" % (result.job_id, result.exit_code, text.splitlines()[0]))
            self._show_info("Plate solution / field of view", text)
        self.app.update_action_sensitivity()

    def action_sky_map(self) -> None:
        if not self.current_paths:
            self._log("Open an image before generating a sky map")
            return
        if not self.registry.available("SkyStacker"):
            self._show_error("SkyStacker is not installed; Gaia sky maps are unavailable.")
            return
        source = self.current_paths[-1]
        output_dir = self._astrometry_job_dir("sky-map")
        self._reuse_plate_solution(source, output_dir)
        argv = self.adapters["SkyStacker"].build_sky_map_argv(
            source, output_dir, self.plate_centers.get(source)
        )
        self._run_astrometry(
            "sky-map",
            argv,
            output_dir,
            lambda result: self._on_sky_map_done(result, output_dir),
        )

    def _on_sky_map_done(self, result, output_dir: str) -> None:
        if not result.ok:
            self._busy_end()
            self._log("CLI %s failed: %s" % (result.job_id, result.error or result.stderr))
            self._show_error("Gaia sky map failed: %s" % (result.error or result.stderr))
            return
        svg = find_output(output_dir, [".svg"])
        if not svg:
            self._busy_end()
            self._show_info("Gaia sky map", "No SVG sky map was written by SkyStacker.")
            return
        png = os.path.join(output_dir, "sky_map.png")
        argv = [self._magick_adapter.binary, svg, png]
        self._log("CLI sky-map-preview: %s" % " ".join(argv))
        self.engine.run(
            "sky-map-preview",
            argv,
            on_log=self._log,
            on_done=lambda preview: self._on_sky_map_preview(preview, png, svg),
        )

    def _on_sky_map_preview(self, result, png: str, svg: str) -> None:
        self._busy_end()
        if result.ok:
            self._show_image("Gaia sky map", png)
        else:
            self._show_info("Gaia sky map", "SVG written at %s (PNG preview failed)" % svg)

    def action_survey_cutout(self) -> None:
        if not self.current_paths:
            self._log("Open an image before requesting a survey cutout")
            return
        if not self.registry.available("SkyStacker"):
            self._show_error("SkyStacker is not installed; survey cutouts are unavailable.")
            return
        source = self.current_paths[-1]
        output_dir = self._astrometry_job_dir("survey-cutout")
        self._reuse_plate_solution(source, output_dir)
        argv = self.adapters["SkyStacker"].build_survey_cutout_argv(
            source, output_dir, plate_center=self.plate_centers.get(source)
        )
        self._run_astrometry(
            "survey-cutout",
            argv,
            output_dir,
            lambda result: self._on_survey_cutout_done(result, output_dir),
        )

    def _on_survey_cutout_done(self, result, output_dir: str) -> None:
        self._busy_end()
        if not result.ok:
            self._log("CLI %s failed: %s" % (result.job_id, result.error or result.stderr))
            self._show_error("Survey cutout failed: %s" % (result.error or result.stderr))
            return
        fits_file = find_output(output_dir, [".fits", ".fit"])
        text = "Survey cutout written to %s" % (fits_file or output_dir)
        self._log("CLI %s exit %d: %s" % (result.job_id, result.exit_code, text))
        self._show_info("Observatory survey cutout", text)

    def action_about(self) -> None:
        dialog = Gtk.AboutDialog()
        dialog.set_transient_for(self)
        dialog.set_modal(True)
        dialog.set_program_name("Astro Studio")
        dialog.set_version(__version__)
        dialog.set_comments(
            "Version %s | Build %s\n"
            "Zero-processing GTK 3.24 front-end that orchestrates external "
            "astronomical and photographic CLI backends."
            % (__version__, BUILD_DATE)
        )
        dialog.set_license_type(Gtk.License.MIT_X11)
        dialog.set_authors(["Astro Studio contributors"])
        dialog.run()
        dialog.destroy()

    def action_settings(self) -> None:
        dialog = Gtk.Dialog(
            title="Backend settings and preferences",
            parent=self,
            modal=True,
            buttons=(
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK,
                Gtk.ResponseType.OK,
            ),
        )
        grid = Gtk.Grid()
        grid.set_border_width(8)
        grid.set_row_spacing(6)
        grid.set_column_spacing(8)
        row = 0

        installed = [
            status
            for status in self.registry.status.values()
            if self.registry.installed(status.name)
        ]
        grid.attach(Gtk.Label(label="Installed connectors", xalign=0.0), 0, row, 2, 1)
        row += 1
        checkboxes = {}
        for status in installed:
            checkbox = Gtk.CheckButton(label=status.name)
            checkbox.set_active(self.settings.is_backend_enabled(status.name))
            grid.attach(checkbox, 0, row, 2, 1)
            checkboxes[status.name] = checkbox
            row += 1

        language = Gtk.ComboBoxText()
        for code in ("en", "es", "de", "ja"):
            language.append_text(code)
        language.set_active(max(0, ("en", "es", "de", "ja").index(self.settings.get("language", "en"))))
        theme = Gtk.ComboBoxText()
        for name in ("system", "dark", "light"):
            theme.append_text(name)
        theme.set_active(max(0, ("system", "dark", "light").index(self.settings.get("theme", "system"))))
        offline = Gtk.CheckButton(label="Offline mode (no catalog downloads)")
        offline.set_active(bool(self.settings.get("offline", False)))
        threads = Gtk.SpinButton.new_with_range(0, 64, 1)
        threads.set_value(int(self.settings.get("threads", 0)))

        for label, widget in (
            ("Language", language),
            ("Theme", theme),
            ("Offline", offline),
            ("Max threads (0 = backend default)", threads),
        ):
            grid.attach(Gtk.Label(label=label, xalign=0.0), 0, row, 1, 1)
            grid.attach(widget, 1, row, 1, 1)
            row += 1

        dialog.get_content_area().pack_start(grid, True, True, 0)
        dialog.show_all()
        if dialog.run() == Gtk.ResponseType.OK:
            for name, checkbox in checkboxes.items():
                self.settings.set_backend_enabled(name, checkbox.get_active())
            self.settings.set("language", language.get_active_text())
            self.settings.set("theme", theme.get_active_text())
            self.settings.set("offline", offline.get_active())
            self.settings.set("threads", int(threads.get_value()))
            self.settings.save()
            self._apply_theme()
            self.app.update_action_sensitivity()
            self._log("Preferences saved to %s" % self.settings.path)
            self._status("Preferences saved")
        dialog.destroy()

    def action_undo(self) -> None:
        if not self.current_images:
            self._log("Open an image before using Undo")
            return
        view_state = self._capture_view_state()
        self.workspace.undo(
            self.current_images[-1],
            on_ready=lambda final: self._on_history_done(final, view_state),
            on_error=self._on_workspace_error,
            on_log=self._log,
        )

    def action_redo(self) -> None:
        if not self.current_images:
            self._log("Open an image before using Redo")
            return
        view_state = self._capture_view_state()
        self.workspace.redo(
            self.current_images[-1],
            on_ready=lambda final: self._on_history_done(final, view_state),
            on_error=self._on_workspace_error,
            on_log=self._log,
        )

    def _on_history_done(self, image: WorkingImage, view_state: dict = None) -> None:
        self.preview.load(image.png_path)
        self._restore_view_state(view_state)
        self._log("History applied to %s; preview refreshed" % image.key)
        self._status_image(image, "History applied (view unchanged)")
        self.app.update_action_sensitivity()

    def action_zoom_in(self) -> None:
        self.preview.zoom_in()
        self._status("Zoom: %.0f%%" % (self.preview.zoom * 100))

    def action_zoom_out(self) -> None:
        self.preview.zoom_out()
        self._status("Zoom: %.0f%%" % (self.preview.zoom * 100))

    def action_zoom_fit(self) -> None:
        self.preview.zoom_fit()
        self._status("Zoom: fit to window")

    def _set_zoom(self, scale: float, label: str) -> None:
        self.preview.set_zoom_scale(scale)
        self._status("Zoom: %s" % label)

    def action_zoom_10(self) -> None:
        self._set_zoom(0.10, "10%")

    def action_zoom_25(self) -> None:
        self._set_zoom(0.25, "25%")

    def action_zoom_50(self) -> None:
        self._set_zoom(0.50, "50%")

    def action_zoom_75(self) -> None:
        self._set_zoom(0.75, "75%")

    def action_zoom_100(self) -> None:
        self._set_zoom(1.0, "100%")

    def action_zoom_150(self) -> None:
        self._set_zoom(1.50, "150%")

    def action_zoom_200(self) -> None:
        self._set_zoom(2.0, "200%")

    def action_zoom_400(self) -> None:
        self._set_zoom(4.0, "400%")

    def action_zoom_1000(self) -> None:
        self._set_zoom(10.0, "1000%")

    def action_zoom_1_1(self) -> None:
        self.preview.set_zoom_scale(1.0)
        self._status("Zoom: 1:1 (one screen pixel per image pixel)")

    def action_quit(self) -> None:
        self.engine.cancel_all()
        self.scratch.cleanup_all()
        self.app.quit()
