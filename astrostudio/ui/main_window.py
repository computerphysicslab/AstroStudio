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
    Translator,
    WorkingImage,
    find_output,
    unique_export_path,
    find_plate_solution,
    histogram_argv,
    cli_entries,
    install_command,
    package_for_binary,
    parse_histogram_text,
    parse_policy,
    solution_for_directory,
    write_makefile,
    write_shell,
    summarize_solution,
)
from .histogram_panel import HistogramWidget  # noqa: E402
from .preview import PreviewPane  # noqa: E402
from .resource_monitor import ResourceMonitor  # noqa: E402
from .window_utils import make_draggable  # noqa: E402

MENU_LAYOUT = (
    (
        "File",
        (
            ("Open", "open"),
            ("Export / Save As", "export"),
            ("Export Pipeline...", "export-pipeline"),
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
                "Resize Image",
                None,
                (
                    ("10%", "resize-10"),
                    ("25%", "resize-25"),
                    ("50%", "resize-50"),
                    ("75%", "resize-75"),
                    ("100%", "resize-100"),
                    ("150%", "resize-150"),
                    ("200%", "resize-200"),
                    ("400%", "resize-400"),
                    ("1000%", "resize-1000"),
                    (None, None),
                    ("Custom Scale...", "resize-custom"),
                ),
            ),
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
            ("Toggle Histogram Viewer", "toggle-histogram"),
            ("Toggle Terminal Drawer", "toggle-terminal"),
        ),
    ),
    (
        "Options",
        (
            ("Backend Settings", "settings"),
            ("Frontend Settings", "frontend-settings"),
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
    "psd",
    "psb",
)

TOOL_ITEMS = (
    ("document-open", "Open", "open"),
    ("document-save-as", "Export", "export"),
    ("dialog-information", "Metadata", "metadata"),
    ("zoom-in", "Zoom in", "zoom-in"),
    ("zoom-out", "Zoom out", "zoom-out"),
    ("zoom-fit-best", "Fit to window", "zoom-fit"),
    ("edit-select-all", "Select Area", "select-area"),
    ("edit-undo", "Undo", "undo"),
    ("edit-redo", "Redo", "redo"),
    ("process-stop", "Stop job", "cancel"),
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


ACCENT_COLORS = {
    "green": "#27ae60",
    "blue": "#2f80ed",
    "orange": "#e67e22",
    "purple": "#8e44ad",
}

TOGGLE_PANELS = {
    "toggle-backends": "Backends Viewer",
    "toggle-histogram": "Histogram Viewer",
    "toggle-terminal": "Terminal Drawer",
}


def toggle_label(action: str, label: str, visible: bool) -> str:
    return "%s: %s" % (label, "On" if visible else "Off")


def append_menu_items(menu: Gio.Menu, items, registry: dict = None, tr=None) -> None:
    translate = tr or (lambda text: text)
    for item in items:
        if item[0] is None:
            menu.append_section(None, Gio.Menu.new())
        elif len(item) == 3:
            child = Gio.Menu.new()
            append_menu_items(child, item[2], registry, translate)
            menu.append_submenu(translate(item[0]), child)
        else:
            menu_item = Gio.MenuItem.new(translate(item[0]), "app." + item[1])
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
        self._last_status = ""
        self._progress_timer = None
        self._progress_reset_timer = None
        self._progress_started = None
        self._progress_estimate = None
        self.registry = registry
        self.scratch = scratch
        self.engine = engine
        self.translator = Translator(self.settings.get("language", "en"))
        for index in range(10):
            setattr(
                self,
                "action_open_recent_%d" % index,
                lambda checked=False, position=index: self._open_recent(position),
            )
        self._magick_adapter = ImageMagickAdapter()
        self.adapters = {
            "ImageMagick": self._magick_adapter,
            "ExifTool": ExifToolAdapter(),
            "SkyStacker": SkyStackerAdapter(),
        }
        from ..adapters.skystacker import discover_catalog_dir

        self.adapters["SkyStacker"].cache_dir = self.settings.get("cache_dir") or None
        self.adapters["SkyStacker"].catalog_dir = (
            self.settings.get("blind_catalog_dir")
            or discover_catalog_dir()
            or None
        )
        transform_cache = self.settings.get("cache_dir") or os.path.join(
            os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache"),
            "astro-studio",
            "transforms",
        )
        self.workspace = ImageWorkspace(
            scratch, engine, self._magick_adapter, cache_dir=transform_cache
        )
        self.current_images: List[WorkingImage] = []
        self.current_paths = []
        self.export_format: ExportFormat = EXPORT_FORMATS[0]
        self.job_counter = 0
        self.plate_solutions: dict = {}
        self.plate_centers: dict = {}
        self.plate_options: dict = {}
        self.package_info: dict = {}
        self.backend_rows: dict = {}
        self.panel_labels: dict = {}
        self.toolbar_buttons: dict = {}
        self.toolbar_labels: dict = {}
        self._accent_provider = None
        self._busy_count = 0
        self.metadata_pending = 0
        self.metadata_window = None
        self.histogram_pending = 0
        self.histogram_generation = 0
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
        self.set_resizable(True)

        self.preview = PreviewPane()
        self.preview.set_size_request(640, 480)
        self.preview.add_events(Gdk.EventMask.SCROLL_MASK)
        self.preview.connect("button-press-event", self._on_canvas_click)
        self.preview.connect("motion-notify-event", self._on_canvas_motion)
        self.preview.connect("button-release-event", self._on_canvas_release)
        self.preview.connect("scroll-event", self._on_preview_scroll)
        self.preview.drag_dest_set(
            Gtk.DestDefaults.ALL,
            [Gtk.TargetEntry.new("text/uri-list", 0, 0)],
            Gdk.DragAction.COPY,
        )
        self.preview.connect("drag-data-received", self._on_drag_data_received)
        self.preview.connect("drag-motion", self._on_drag_motion)

        self._build_layout()
        self._apply_theme()
        self._apply_font()
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
        self.histogram_widget = HistogramWidget()
        self.histogram_widget.on_change = self._on_stretch_change
        self.histogram_panel = self._panel_with_close(
            "Histogram (CLI data, click handles to stretch)", self.histogram_widget
        )
        self.terminal_panel = self._panel_with_close(
            "Terminal Drawer", self._build_log_content()
        )
        right.pack_start(self.backends_panel, False, False, 0)
        right.pack_start(self.metadata_panel, False, False, 0)
        right.pack_start(self.histogram_panel, False, False, 0)
        right.pack_start(self.terminal_panel, True, True, 0)
        paned.pack2(right, False, True)
        root.pack_start(paned, True, True, 0)

        self._apply_progress_css()
        self.progress_bar = Gtk.ProgressBar()
        self.progress_bar.set_size_request(-1, 18)
        self.progress_bar.set_show_text(True)
        self.progress_bar.override_font(Pango.FontDescription("Sans 11"))
        self._last_status = self.translator.tr("Astro Studio ready")
        self.progress_bar.set_text(self._last_status)
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
                    {
                        "toggle-backends": "backends_panel",
                        "toggle-histogram": "histogram_panel",
                        "toggle-terminal": "terminal_panel",
                    }[item[1]],
                    None,
                )
                visible = panel.get_visible() if panel is not None else True
                result.append(
                    (
                        toggle_label(
                            item[1],
                            self.translator.tr(TOGGLE_PANELS[item[1]]),
                            visible,
                        ),
                        item[1],
                    )
                )
            else:
                result.append(item)
        return result

    def _build_menu_bar(self) -> Gtk.Widget:
        menu = Gio.Menu.new()
        for label, entries in MENU_LAYOUT:
            submenu = Gio.Menu.new()
            append_menu_items(
                submenu, self._dynamic_entries(entries), self._menu_items, self.translator.tr
            )
            if label == "File":
                recent_menu = Gio.Menu.new()
                paths = self.settings.get("recent_images", [])
                if paths:
                    for index, path in enumerate(paths[:10]):
                        recent_menu.append(
                            os.path.basename(path), "app.open-recent-%d" % index
                        )
                else:
                    recent_menu.append(self.translator.tr("No recent images"), "app.open")
                submenu.append_submenu(self.translator.tr("Open Recent"), recent_menu)
            menu.append_submenu(self.translator.tr(label), submenu)
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
                Gtk.Image.new_from_icon_name(icon, Gtk.IconSize.BUTTON),
                self.translator.tr(label),
            )
            button.set_tooltip_text(self.translator.tr(label))
            button.connect("clicked", lambda *_widget, name=action: self._activate(name))
            self.toolbar_buttons[action] = button
            self.toolbar_labels[action] = label
            toolbar.insert(button, -1)
        return toolbar

    def _panel_with_close(self, title: str, content: Gtk.Widget) -> Gtk.Widget:
        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        header.set_size_request(-1, 16)
        label = Gtk.Label(label=self.translator.tr(title), xalign=0.0)
        self.panel_labels[title] = label
        label.set_hexpand(True)
        label.set_margin_top(0)
        label.set_margin_bottom(0)
        label.override_font(Pango.FontDescription("sans 9"))
        close_button = Gtk.Button.new_from_icon_name(
            "window-close-symbolic", Gtk.IconSize.MENU
        )
        close_button.set_relief(Gtk.ReliefStyle.NONE)
        close_button.set_size_request(16, 14)
        close_button.set_tooltip_text("Close panel")
        close_button.connect("clicked", lambda *_: self._on_panel_closed(panel))
        header.pack_start(label, True, True, 0)
        header.pack_start(close_button, False, False, 0)
        panel.pack_start(header, False, False, 0)
        panel.pack_start(content, True, True, 0)
        return panel

    def _build_backend_content(self) -> Gtk.Widget:
        self.backend_store = Gtk.ListStore(GdkPixbuf.Pixbuf, str, str)
        view = Gtk.TreeView(model=self.backend_store)
        view.append_column(
            Gtk.TreeViewColumn("", Gtk.CellRendererPixbuf(), pixbuf=0)
        )
        for index, title in ((1, "Name"), (2, "Version")):
            view.append_column(
                Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=index)
            )
        view.connect("row-activated", self._on_backend_activated)
        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(130)
        scroll.add(view)
        return scroll

    @staticmethod
    def _backend_icon(available: bool) -> GdkPixbuf.Pixbuf:
        name = "dialog-ok" if available else "dialog-error"
        theme = Gtk.IconTheme.get_default()
        try:
            return theme.load_icon(name, 16, 0)
        except GLib.Error:
            return None

    def _on_backend_activated(self, _view, path, _column) -> None:
        row = self.backend_store[path]
        name = row[1]
        status = self.registry.status.get(name)
        if status is None:
            return
        package = package_for_binary(os.path.basename(status.binary))
        info = self.package_info.get(name)
        if info is None:
            job_id = "probe-package-" + name.replace(" ", "-")
            self.engine.run(
                job_id,
                ["apt-cache", "policy", package],
                on_done=lambda result: self._on_package_info(name, package, status, result),
            )
            self._log("Querying apt-cache for %s..." % package)
            return
        self._show_backend_info(name, status, package, info)

    def _on_package_info(self, name: str, package: str, status, result) -> None:
        installed, candidate = parse_policy(result.stdout)
        self.package_info[name] = (installed, candidate)
        self._show_backend_info(name, status, package, (installed, candidate))

    def _show_backend_info(self, name: str, status, package: str, info) -> None:
        installed, candidate = info
        command = install_command(status.binary)
        window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        window.set_title("%s details" % name)
        window.set_transient_for(self)
        window.set_modal(True)
        window.set_default_size(520, 300)
        header = Gtk.HeaderBar()
        header.set_title("%s details" % name)
        header.set_show_close_button(True)
        window.set_titlebar(header)
        make_draggable(window, header)

        grid = Gtk.Grid()
        grid.set_border_width(12)
        grid.set_row_spacing(6)
        grid.set_column_spacing(10)
        facts = (
            ("Connector", name),
            ("Binary", status.binary),
            ("Detected version", status.version or "unknown"),
            ("apt package", package),
            ("apt installed", installed or "not installed"),
            ("apt candidate", candidate or "unknown"),
            (
                "Action",
                "not installed" if not self.registry.installed(name)
                else "upgrade available" if candidate and installed and candidate != installed
                else "up to date",
            ),
        )
        for row, (label, value) in enumerate(facts):
            grid.attach(Gtk.Label(label=label, xalign=0.0), 0, row, 1, 1)
            grid.attach(Gtk.Label(label=value, xalign=0.0, selectable=True), 1, row, 1, 1)

        command_entry = Gtk.Entry()
        command_entry.set_text(command)
        command_entry.set_editable(False)
        copy_button = Gtk.Button(label="Copy command")
        copy_button.connect(
            "clicked",
            lambda *_: Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD).set_text(command, -1),
        )
        grid.attach(Gtk.Label(label="Shell command", xalign=0.0), 0, len(facts), 1, 1)
        grid.attach(command_entry, 1, len(facts), 1, 1)
        grid.attach(copy_button, 1, len(facts) + 1, 1, 1)
        window.add(grid)
        loop = GLib.MainLoop()
        window.connect("delete-event", lambda *_: (loop.quit(), True)[1])
        copy_button.connect("clicked", lambda *_: self._log("Copied: %s" % command))
        window.show_all()
        loop.run()
        window.destroy()

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

    def _apply_progress_css(self) -> None:
        colour = ACCENT_COLORS.get(
            self.settings.get("accent_color", "green"), ACCENT_COLORS["green"]
        )
        css = """
progressbar {
    font-size: 13px;
    border: none;
    border-radius: 0;
}
progressbar, progressbar trough, progressbar progress {
    min-height: 18px;
    border-radius: 0;
}
progressbar trough {
    background-color: #2b2b2b;
    border: none;
}
progressbar progress {
    background-color: %s;
    border: none;
}
progressbar text {
    color: #ffffff;
}
""" % colour
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode("utf-8"))
        screen = Gdk.Screen.get_default()
        if screen is not None:
            if self._accent_provider is not None:
                Gtk.StyleContext.remove_provider_for_screen(screen, self._accent_provider)
            Gtk.StyleContext.add_provider_for_screen(
                screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            self._accent_provider = provider

    def _apply_font(self) -> None:
        gtk_settings = Gtk.Settings.get_default()
        if gtk_settings is None:
            return
        size = int(self.settings.get("font_size", 9))
        gtk_settings.set_property("gtk-font-name", "Sans %d" % max(7, min(18, size)))

    def _apply_language(self) -> None:
        self.translator = Translator(self.settings.get("language", "en"))
        for title, label in self.panel_labels.items():
            label.set_text(self.translator.tr(title))
        for action, button in self.toolbar_buttons.items():
            text = self.translator.tr(self.toolbar_labels[action])
            button.set_label(text)
            button.set_tooltip_text(text)
        self._rebuild_menu_bar()

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

    def _on_drag_motion(self, _widget, _context, _x, _y, _time) -> bool:
        return True

    def _on_drag_data_received(self, _widget, _context, _x, _y, data, _info, _time) -> None:
        uris = list(data.get_uris() or [])
        if not uris:
            uris = [
                line.strip()
                for line in (data.get_text() or "").splitlines()
                if line.strip().startswith("file://")
            ]
        self._log("Dropped %d URI(s)" % len(uris))
        for uri in uris:
            path = Gio.File.new_for_uri(uri).get_path()
            if not path:
                continue
            if os.path.isdir(path):
                for name in sorted(os.listdir(path)):
                    child = os.path.join(path, name)
                    if os.path.isfile(child) and name.rsplit(".", 1)[-1].lower() in IMAGE_EXTENSIONS:
                        self._open_file(child)
            elif os.path.isfile(path):
                self._open_file(path)

    def _update_toggle_labels(self) -> None:
        self._rebuild_menu_bar()

    def _activate(self, action: str) -> None:
        gio_action = self.app.lookup_action(action)
        if gio_action is not None and not gio_action.get_enabled():
            self._log("Action unavailable: %s (check Backends panel)" % action)
            self._status("%s: %s" % (self.translator.tr("Action unavailable"), action))
            return
        self.app.activate_action(action, None)

    def _status(self, text: str) -> None:
        self._last_status = text
        if self._progress_started is None and self._progress_timer is None:
            self.progress_bar.set_text(text)

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
        self._stop_progress()
        seconds = self.estimator.estimate(stage, megapixels)
        self._estimate_stage = stage
        self._estimate_mp = megapixels
        self._estimate_s = seconds
        self._progress_started = time.monotonic()
        self._progress_estimate = seconds
        self.operation_log.record(
            "estimate", stage=stage, megapixels=megapixels, estimate_s=seconds
        )
        if seconds is None:
            self._status(message)
            self.progress_bar.set_text("Working...")
            self._progress_timer = GLib.timeout_add(100, self._pulse_progress)
            return
        self._status("%s (est. %.1f s)" % (message, seconds))
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_text("0%% (est. %.1f s)" % seconds)
        self._progress_timer = GLib.timeout_add(100, self._tick_progress)

    def _pulse_progress(self) -> bool:
        self.progress_bar.pulse()
        return True

    def _tick_progress(self) -> bool:
        if self._progress_started is None or not self._progress_estimate:
            return False
        elapsed = time.monotonic() - self._progress_started
        fraction = min(1.0, elapsed / self._progress_estimate)
        self.progress_bar.set_fraction(fraction)
        self.progress_bar.set_text(
            "%.0f%% (est. %.1f s)" % (fraction * 100, self._progress_estimate)
        )
        return True

    def _reset_progress(self) -> bool:
        self._progress_reset_timer = None
        self.progress_bar.set_fraction(0.0)
        self.progress_bar.set_text(self._last_status)
        return False

    def _stop_progress(self) -> None:
        if self._progress_reset_timer is not None:
            GLib.source_remove(self._progress_reset_timer)
            self._progress_reset_timer = None
        if self._progress_timer is not None:
            GLib.source_remove(self._progress_timer)
            self._progress_timer = None
        started = self._progress_started
        estimate = self._progress_estimate
        self._progress_started = None
        self._progress_estimate = None
        if started is None:
            self.progress_bar.set_fraction(0.0)
            self.progress_bar.set_text("")
            return
        actual = time.monotonic() - started
        self.operation_log.record(
            "estimate_result",
            stage=self._estimate_stage,
            megapixels=self._estimate_mp,
            estimate_s=estimate,
            actual_s=round(actual, 3),
        )
        self.progress_bar.set_fraction(1.0)
        self.progress_bar.set_text("Done in %.1f s" % actual)
        self._progress_reset_timer = GLib.timeout_add(1200, self._reset_progress)

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
        self._dialog_header(dialog, "Error")
        dialog.run()
        dialog.destroy()

    def _on_canvas_click(self, widget, event) -> bool:
        button = event.button
        if not isinstance(button, int):
            button = button.button
        if event.type == Gdk.EventType.DOUBLE_BUTTON_PRESS and button == 1:
            self.action_zoom_fit()
            return True
        if self.preview.select_mode and button == 1:
            self.preview.start_selection(event.x, event.y)
            return True
        position = self.preview.image_coordinates(event.x, event.y)
        if position:
            self._status(
                "X=%d  Y=%d (%s)" % (position[0], position[1], self.translator.tr("drag to pan"))
            )
        if button == 1:
            self.preview.start_pan(event.x, event.y)
        return True

    def _on_canvas_motion(self, widget, event) -> bool:
        if self.preview.select_mode:
            self.preview.update_selection(event.x, event.y)
            return True
        return self.preview.update_pan(event.x, event.y)

    def _on_canvas_release(self, widget, event) -> bool:
        if self.preview.select_mode:
            rectangle = self.preview.finish_selection()
            if rectangle:
                self._log("Selected area: %s" % (rectangle,))
                self._status("Selection: %dx%d" % (rectangle[2], rectangle[3]))
            return True
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
        self._status("%s: %s (mouse wheel)" % (self.translator.tr("Zoom"), zoom))
        return True

    def on_backends_updated(self, registry) -> None:
        self.backend_store.clear()
        statuses = sorted(
            registry.status.values(),
            key=lambda status: (not status.available, status.name.lower()),
        )
        self.backend_rows.clear()
        for status in statuses:
            row = self.backend_store.append(
                (self._backend_icon(status.available), status.name, status.version or "-")
            )
            self.backend_rows[status.name] = row
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

    def _remember_recent(self, path: str) -> None:
        recent = [item for item in self.settings.get("recent_images", []) if item != path]
        recent.insert(0, path)
        self.settings.set("recent_images", recent[:10])
        self.settings.save()
        self._rebuild_menu_bar()

    def _open_recent(self, index: int) -> None:
        recent = self.settings.get("recent_images", [])
        if index >= len(recent):
            return
        path = recent[index]
        if os.path.isfile(path):
            self._open_file(path)
        else:
            self._log("Recent file no longer exists: %s" % path)

    def _open_file(self, path: str) -> None:
        if not self.registry.available("ImageMagick"):
            self._log("Backend unavailable: ImageMagick is required for the TIFF workspace")
            return
        if path.lower().endswith(".cr2") and not self.registry.available("SkyStacker"):
            self._show_error("SkyStacker is required to decode Canon CR2 files.")
            return
        self.current_paths.append(path)
        self._remember_recent(path)
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
        self._status_image(image, "%s: %s" % (self.translator.tr("Ready"), os.path.basename(image.source)))
        self._log(
            "Workspace ready: TIFF=%s | PNG=%s"
            % (image.tiff_path, image.png_path)
        )
        self._compute_histogram(image)

    def _on_workspace_error(self, message: str) -> None:
        self._busy_end()
        self._stop_progress()
        if "cancel" in message.lower():
            self._status(self.translator.tr("Process stopped (OK)"))
            self._log("Process stopped by user (OK)")
            return
        self._status(self.translator.tr("Workspace error"))
        self._log(message)
        self._show_error(message)

    def action_export_pipeline(self) -> None:
        dialog = Gtk.FileChooserDialog(
            title="Export pipeline",
            parent=self,
            action=Gtk.FileChooserAction.SAVE,
            buttons=(
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_SAVE,
                Gtk.ResponseType.OK,
            ),
        )
        dialog.set_current_name("pipeline.sh")
        dialog.set_do_overwrite_confirmation(True)
        response = dialog.run()
        path = dialog.get_filename() if response == Gtk.ResponseType.OK else None
        dialog.destroy()
        if not path:
            return
        jobs = cli_entries(self.operation_log.entries(), self.operation_log.session)
        if path.endswith(".mk") or path.endswith("Makefile"):
            write_makefile(jobs, path)
        else:
            if not path.endswith(".sh"):
                path += ".sh"
            write_shell(jobs, path)
        self._log("Exported %d CLI jobs to %s" % (len(jobs), path))
        self._status("Pipeline exported (%d jobs)" % len(jobs))

    def action_export(self) -> None:
        if not self.current_images:
            self._log("Open an image before exporting")
            self._status(self.translator.tr("Open an image before exporting"))
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
            "%s: %s (%.2f MB, %.1f s)"
            % (
                self.translator.tr("Export complete"),
                os.path.basename(destination),
                size_mb,
                elapsed,
            )
        )
        self.app.update_action_sensitivity()

    def _run_transform(self, params: dict, description: str) -> None:
        if not self.current_images:
            self._log("Open an image before applying a transformation")
            self._status(self.translator.tr("Open an image first"))
            return
        if not self.registry.available("ImageMagick"):
            self._log("Backend unavailable: ImageMagick is required for transformations")
            return
        image = self.current_images[-1]
        view_state = self._capture_view_state()
        started = time.monotonic()
        self._busy_begin()
        stage = next(iter(params), "transform")
        if stage == "resize":
            try:
                percent = float(str(params["resize"]).rstrip("%"))
                stage = "resize-up" if percent >= 100 else "resize-down"
            except ValueError:
                stage = "resize-down"
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
            image, "%s %.1f s (%s)" % (
                self.translator.tr("Transform applied in"),
                elapsed,
                self.translator.tr("view unchanged"),
            )
        )
        self.app.update_action_sensitivity()

    def _ask_percentage(self) -> Optional[str]:
        window = Gtk.Window(type=Gtk.WindowType.TOPLEVEL)
        window.set_title(self.translator.tr("Resize image"))
        window.set_transient_for(self)
        window.set_modal(True)
        window.set_default_size(320, 110)
        header = Gtk.HeaderBar()
        header.set_title(self.translator.tr("Resize image"))
        header.set_show_close_button(False)
        cancel = Gtk.Button(label=self.translator.tr("Cancel"))
        ok = Gtk.Button(label=self.translator.tr("OK"))
        ok.get_style_context().add_class("suggested-action")
        header.pack_start(cancel)
        header.pack_end(ok)
        window.set_titlebar(header)
        make_draggable(window, header)

        entry = Gtk.Entry()
        entry.set_text("50")
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        box.set_border_width(12)
        box.pack_start(Gtk.Label(label="Scale (%)"), False, False, 0)
        box.pack_start(entry, True, True, 0)
        window.add(box)

        loop = GLib.MainLoop()
        accepted = {"value": False}

        def finish(_button) -> None:
            accepted["value"] = _button is ok
            loop.quit()

        cancel.connect("clicked", finish)
        ok.connect("clicked", finish)
        window.connect("delete-event", lambda *_: (loop.quit(), True)[1])
        window.show_all()
        loop.run()
        window.destroy()

        if not accepted["value"]:
            return None
        text = entry.get_text().strip().rstrip("%")
        try:
            number = float(text)
        except ValueError:
            number = 0.0
        if 0 < number <= 10000:
            return "%g%%" % number
        self._log("Invalid scale; enter a percentage between 0 and 10000")
        return None

    def _resize_to(self, percent: int) -> None:
        scale = "%d%%" % percent
        self._run_transform({"resize": scale}, "Resize to " + scale)

    def action_resize_10(self) -> None:
        self._resize_to(10)

    def action_resize_25(self) -> None:
        self._resize_to(25)

    def action_resize_50(self) -> None:
        self._resize_to(50)

    def action_resize_75(self) -> None:
        self._resize_to(75)

    def action_resize_100(self) -> None:
        self._resize_to(100)

    def action_resize_150(self) -> None:
        self._resize_to(150)

    def action_resize_200(self) -> None:
        self._resize_to(200)

    def action_resize_400(self) -> None:
        self._resize_to(400)

    def action_resize_1000(self) -> None:
        self._resize_to(1000)

    def action_resize_custom(self) -> None:
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
        self._dialog_header(dialog, "Sharpen image")
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
        self._dialog_header(dialog, "Choose export format")
        dialog.set_default_size(600, 560)
        dialog.set_decorated(True)

        store = Gtk.ListStore(str, str, str)
        for export_format in EXPORT_FORMATS:
            store.append((export_format.key, export_format.label, export_format.category))
        view = Gtk.TreeView(model=store)
        renderer = Gtk.CellRendererText()
        renderer.set_property("font", "Sans 9")
        view.append_column(Gtk.TreeViewColumn("Format", renderer, text=1))
        view.append_column(Gtk.TreeViewColumn("Type", Gtk.CellRendererText(), text=2))
        view.connect("row-activated", lambda *_: dialog.response(Gtk.ResponseType.OK))
        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_width(520)
        scroll.set_min_content_height(480)
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
            self._status(self.translator.tr("Open an image first"))
            return
        image = self.current_images[-1]
        self.metadata_pending = 2
        self._read_metadata(image.png_path, "png", "PNG preview")
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
            self._status("%s: %s" % (self.translator.tr("Metadata loaded"), label))
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
        window.set_title(self.translator.tr("Metadata - Astro Studio"))
        window.set_transient_for(self)
        window.set_modal(False)
        window.set_default_size(560, 380)
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
        make_draggable(window, header)

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
            self._status(self.translator.tr("Open an image first"))
            return
        self.histogram_panel.show()
        self._update_toggle_labels()
        self._compute_histogram(self.current_images[-1])

    def _compute_histogram(self, image: WorkingImage) -> None:
        if not self.registry.available("ImageMagick"):
            self._log("ImageMagick unavailable; histogram skipped")
            return
        self.histogram_generation += 1
        generation = self.histogram_generation
        self.histogram_widget.set_points(*(image.stretch_points or (0.0, 255.0)))
        self.histogram_pending = 2
        self.histogram_datasets = []
        self.histogram_widget.set_datasets([])
        self._busy_begin()
        self._status(self.translator.tr("Computing histograms via external CLI..."))
        for key, path, label, colour in (
            ("preview", image.png_path, "Displayed PNG", (0.30, 0.65, 1.0)),
            ("working", image.tiff_path, "Working TIFF", (0.35, 0.85, 0.45)),
        ):
            argv = histogram_argv(self._magick_adapter.binary, path)
            self._log("CLI histogram-%s: %s" % (key, " ".join(argv)))
            self.job_counter += 1
            job_id = "histogram-%s-%d" % (key, self.job_counter)
            self.engine.run(
                job_id,
                argv,
                on_done=lambda result, k=key, p=path, l=label, c=colour, g=generation: self._on_histogram_done(
                    result, k, p, l, c, g
                ),
            )

    def _on_histogram_done(self, result, key: str, path: str, label: str, colour, generation: int = 0) -> None:
        if generation != self.histogram_generation:
            return
        if result.ok:
            points = parse_histogram_text(result.stdout)
            self.histogram_datasets.append((label, colour, points))
            self._log("CLI %s exit %d (%d bins)" % (result.job_id, result.exit_code, len(points)))
        else:
            self._log("CLI %s failed: %s" % (result.job_id, result.error or result.stderr))
        self.histogram_pending -= 1
        if self.histogram_pending == 0:
            self._busy_end()
            self.histogram_widget.set_datasets(self.histogram_datasets)
            self._status(self.translator.tr("Histogram ready (drag the two handles to stretch)"))

    def _on_stretch_change(self, low: float, high: float) -> None:
        if not self.current_images:
            return
        image = self.current_images[-1]
        image.stretch_points = (low, high)
        view_state = self._capture_view_state()
        self.workspace.update_preview(
            image,
            on_ready=lambda final: self._on_stretch_preview_ready(final, view_state, low, high),
            on_error=self._on_workspace_error,
            on_log=self._log,
        )

    def _on_stretch_preview_ready(self, image: WorkingImage, view_state: dict, low: float, high: float) -> None:
        self.preview.load(image.png_path)
        self._restore_view_state(view_state)
        self._log("Display stretch applied: low %.0f, high %.0f (TIFF untouched)" % (low, high))
        self._status_image(image, "%s %.0f-%.0f (%s)" % (self.translator.tr("Display stretch"), low, high, self.translator.tr("view unchanged")))

    def _on_panel_closed(self, panel) -> None:
        panel.hide()
        self._update_toggle_labels()

    def action_toggle_backends(self) -> None:
        if self.backends_panel.get_visible():
            self.backends_panel.hide()
        else:
            self.backends_panel.show()
        self._update_toggle_labels()

    def action_select_area(self) -> None:
        enabled = not self.preview.select_mode
        self.preview.set_select_mode(enabled)
        self._status(
            self.translator.tr("Select Area") + (": ON" if enabled else ": OFF")
        )

    def action_cancel(self) -> None:
        jobs = self.engine.active_jobs
        for job_id in jobs:
            self.engine.cancel(job_id)
        if jobs:
            self._log("Stopped jobs: %s" % ", ".join(jobs))
            self._status("%s %d" % (self.translator.tr("Stopped"), len(jobs)))
            self._stop_progress()
        self.app.update_action_sensitivity()

    def action_toggle_histogram(self) -> None:
        if self.histogram_panel.get_visible():
            self.histogram_panel.hide()
        else:
            self.histogram_panel.show()
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
        self._status(self.translator.tr("Closed active view"))

    def action_close_all(self) -> None:
        self.current_paths.clear()
        self.current_images.clear()
        self.preview.clear()
        self._status(self.translator.tr("All views closed"))

    def _dialog_header(self, dialog: Gtk.Window, title: str) -> Gtk.HeaderBar:
        header = Gtk.HeaderBar()
        header.set_title(self.translator.tr(title))
        header.set_show_close_button(True)
        dialog.set_titlebar(header)
        make_draggable(dialog, header)
        return header

    def _show_info(self, title: str, text: str) -> None:
        dialog = Gtk.MessageDialog(
            parent=self,
            modal=True,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=title,
        )
        self._dialog_header(dialog, title)
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
        self._dialog_header(dialog, title)
        dialog.add_button(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)
        image = Gtk.Image.new_from_pixbuf(pixbuf)
        dialog.get_content_area().pack_start(image, True, True, 6)
        dialog.show_all()
        dialog.run()
        dialog.destroy()

    def _ask_plate_solver_options(self) -> Optional[dict]:
        dialog = Gtk.Dialog(
            title="Plate solving options",
            parent=self,
            modal=True,
            buttons=(
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK,
                Gtk.ResponseType.OK,
            ),
        )
        self._dialog_header(dialog, "Plate solving options")
        ra_entry = Gtk.Entry()
        dec_entry = Gtk.Entry()
        focal_entry = Gtk.Entry()
        pixel_entry = Gtk.Entry()
        catalog_entry = Gtk.Entry()
        catalog_entry.set_text(self.settings.get("blind_catalog", "mag07"))
        catalog_entry.set_placeholder_text("Blind catalog (native solver)")
        solver_combo = Gtk.ComboBoxText()
        for name in ("auto", "gaia", "astrometry-local", "astap", "native", "astrometry-web"):
            solver_combo.append_text(name)
        solver_combo.set_active(0)
        ra_entry.set_placeholder_text("RA degrees (e.g. 83.822)")
        dec_entry.set_placeholder_text("Dec degrees (e.g. -5.391)")
        focal_entry.set_placeholder_text("Focal length mm (optional scale hint)")
        pixel_entry.set_placeholder_text("Pixel size um (optional scale hint)")
        grid = Gtk.Grid()
        grid.set_border_width(6)
        grid.set_row_spacing(4)
        grid.set_column_spacing(8)
        for row, (label, widget) in enumerate(
            (
                ("RA (deg)", ra_entry),
                ("Dec", dec_entry),
                ("Solver", solver_combo),
                ("Blind catalog", catalog_entry),
                ("Focal length (mm)", focal_entry),
                ("Pixel size (um)", pixel_entry),
            )
        ):
            grid.attach(Gtk.Label(label=label, xalign=0.0), 0, row, 1, 1)
            grid.attach(widget, 1, row, 1, 1)
        dialog.get_content_area().pack_start(grid, True, True, 6)
        dialog.show_all()
        options = None
        if dialog.run() == Gtk.ResponseType.OK:
            ra_text = ra_entry.get_text().strip()
            dec_text = dec_entry.get_text().strip()
            center = None
            if ra_text or dec_text:
                try:
                    float(ra_text)
                    float(dec_text)
                    center = "%s,%s" % (ra_text, dec_text)
                except ValueError:
                    self._show_error("RA and Dec must be decimal degrees")
            options = {
                "center": center,
                "solver": solver_combo.get_active_text() or "auto",
                "catalog": catalog_entry.get_text().strip() or "mag07",
                "focal": focal_entry.get_text().strip(),
                "pixel": pixel_entry.get_text().strip(),
            }
        dialog.destroy()
        return options

    def _run_astrometry(self, job_name: str, argv: List[str], output_dir: str, on_done) -> None:
        self.job_counter += 1
        job_id = "%s-%d" % (job_name, self.job_counter)
        self._log("CLI %s: %s" % (job_id, " ".join(argv)))
        self._busy_begin()
        self._status("%s %s" % (self.translator.tr("Running"), job_name))
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
        options = self._ask_plate_solver_options()
        if options is None:
            return
        source = self.current_paths[-1]
        self.plate_options[source] = options
        self.plate_centers[source] = options["center"]
        output_dir = self._astrometry_job_dir("plate-solve")
        adapter = self.adapters["SkyStacker"]
        if options["solver"] == "native":
            argv = adapter.build_blind_solve_argv(
                source,
                output_dir,
                catalog=options["catalog"],
                focal_length=options["focal"],
                pixel_size=options["pixel"],
            )
        else:
            argv = adapter.build_plate_solve_argv(
                source,
                output_dir,
                plate_center=options["center"],
                solver=options["solver"],
                offline=bool(self.settings.get("offline", False)),
                focal_length=options["focal"],
                pixel_size=options["pixel"],
            )
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
            width = self.preview.pixbuf.get_width() if self.preview.pixbuf else 0
            height = self.preview.pixbuf.get_height() if self.preview.pixbuf else 0
            parsed = solution_for_directory(output_dir, width, height)
            if parsed is not None:
                text = parsed.summary()
            else:
                text = summarize_solution(solution) if solution else "No plate_solution.json was written (check star field and seed)."
                text = "Solution could not be parsed:\n" + text
            self._log("CLI %s exit %d; %s" % (result.job_id, result.exit_code, text.splitlines()[0]))
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
        options = self.plate_options.get(source, {})
        argv = self.adapters["SkyStacker"].build_sky_map_argv(
            source,
            output_dir,
            plate_center=options.get("center"),
            solver=options.get("solver", "auto"),
            offline=bool(self.settings.get("offline", False)),
            focal_length=options.get("focal"),
            pixel_size=options.get("pixel"),
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

    def action_frontend_settings(self) -> None:
        dialog = Gtk.Dialog(
            title="Frontend settings",
            parent=self,
            modal=True,
            buttons=(
                Gtk.STOCK_CANCEL,
                Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK,
                Gtk.ResponseType.OK,
            ),
        )
        self._dialog_header(dialog, "Frontend settings")
        grid = Gtk.Grid()
        grid.set_border_width(10)
        grid.set_row_spacing(6)
        grid.set_column_spacing(8)

        language = Gtk.ComboBoxText()
        languages = ("en", "es", "de", "ja", "ru", "zh")
        for code in languages:
            language.append_text(code)
        current_language = self.settings.get("language", "en")
        language.set_active(max(0, languages.index(current_language)))
        theme = Gtk.ComboBoxText()
        for name in ("system", "dark", "light"):
            theme.append_text(name)
        theme.set_active(max(0, ("system", "dark", "light").index(self.settings.get("theme", "system"))))
        accent = Gtk.ComboBoxText()
        for name in ACCENT_COLORS:
            accent.append_text(name)
        accent.set_active(
            max(0, list(ACCENT_COLORS).index(self.settings.get("accent_color", "green")))
        )
        font_size = Gtk.SpinButton.new_with_range(7, 18, 1)
        font_size.set_value(int(self.settings.get("font_size", 9)))

        from ..app import DEFAULT_SHORTCUTS

        shortcut_entries = {}
        custom_shortcuts = self.settings.get("shortcuts", {})
        items = [
            ("Language", language),
            ("Theme", theme),
            ("Accent colour", accent),
            ("Application font size", font_size),
        ]
        for action, default in DEFAULT_SHORTCUTS.items():
            entry = Gtk.Entry()
            current = custom_shortcuts.get(action, default)
            entry.set_text(current[0] if isinstance(current, (list, tuple)) else str(current))
            entry.set_placeholder_text(default[0])
            shortcut_entries[action] = entry
            items.append((action + " shortcut", entry))

        for row, (label, widget) in enumerate(items):
            grid.attach(Gtk.Label(label=label, xalign=0.0), 0, row, 1, 1)
            grid.attach(widget, 1, row, 1, 1)
        dialog.get_content_area().pack_start(grid, True, True, 0)
        dialog.show_all()
        if dialog.run() == Gtk.ResponseType.OK:
            self.settings.set("language", language.get_active_text())
            self.settings.set("theme", theme.get_active_text())
            self.settings.set("accent_color", accent.get_active_text() or "green")
            self.settings.set("font_size", int(font_size.get_value()))
            self.settings.set(
                "shortcuts",
                {
                    action: [entry.get_text().strip()]
                    for action, entry in shortcut_entries.items()
                    if entry.get_text().strip()
                },
            )
            self.settings.save()
            self.app.apply_shortcuts()
            self._apply_language()
            self._apply_theme()
            self._apply_font()
            self._apply_progress_css()
            self._status(self.translator.tr("Preferences saved"))
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
        self._dialog_header(dialog, "Backend settings")
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
        overrides = {}
        for status in installed:
            checkbox = Gtk.CheckButton(label=status.name)
            checkbox.set_active(self.settings.is_backend_enabled(status.name))
            grid.attach(checkbox, 0, row, 1, 1)
            override = Gtk.Entry()
            override.set_text(self.settings.get("binary_overrides", {}).get(status.name, ""))
            override.set_placeholder_text("binary path override")
            grid.attach(override, 1, row, 1, 1)
            checkboxes[status.name] = checkbox
            overrides[status.name] = override
            row += 1

        scratch_entry = Gtk.Entry()
        scratch_entry.set_text(self.settings.get("scratch_dir", ""))
        scratch_entry.set_placeholder_text("scratch root (empty = XDG runtime)")
        cache_entry = Gtk.Entry()
        cache_entry.set_text(self.settings.get("cache_dir", ""))
        cache_entry.set_placeholder_text("Gaia cache directory")
        offline = Gtk.CheckButton(label="Offline mode (no catalog downloads)")
        offline.set_active(bool(self.settings.get("offline", False)))
        threads = Gtk.SpinButton.new_with_range(0, 64, 1)
        threads.set_value(int(self.settings.get("threads", 0)))

        for label, widget in (
            ("Scratch directory", scratch_entry),
            ("Gaia cache directory", cache_entry),
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
            self.settings.set(
                "binary_overrides",
                {name: entry.get_text().strip() for name, entry in overrides.items()},
            )
            self.settings.set("scratch_dir", scratch_entry.get_text().strip())
            self.settings.set("cache_dir", cache_entry.get_text().strip())
            self.settings.set("offline", offline.get_active())
            self.settings.set("threads", int(threads.get_value()))
            self.settings.save()
            self.adapters["SkyStacker"].cache_dir = (
                self.settings.get("cache_dir") or None
            )
            self.app.update_action_sensitivity()
            self._log("Preferences saved to %s" % self.settings.path)
            self._status(self.translator.tr("Preferences saved"))
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
        self._status_image(image, self.translator.tr("History applied (view unchanged)"))
        self.app.update_action_sensitivity()

    def action_zoom_in(self) -> None:
        self.preview.zoom_in()
        self._status("%s: %.0f%%" % (self.translator.tr("Zoom"), self.preview.zoom * 100))

    def action_zoom_out(self) -> None:
        self.preview.zoom_out()
        self._status("%s: %.0f%%" % (self.translator.tr("Zoom"), self.preview.zoom * 100))

    def action_zoom_fit(self) -> None:
        self.preview.zoom_fit()
        self._status("%s: %s" % (self.translator.tr("Zoom"), self.translator.tr("fit to window")))

    def _set_zoom(self, scale: float, label: str) -> None:
        self.preview.set_zoom_scale(scale)
        self._status("%s: %s" % (self.translator.tr("Zoom"), label))

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
        self._status("%s: 1:1 (one screen pixel per image pixel)" % self.translator.tr("Zoom"))

    def action_quit(self) -> None:
        self.engine.cancel_all()
        self.scratch.cleanup_all()
        self.app.quit()
