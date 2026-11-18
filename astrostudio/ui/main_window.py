"""Main GTK window: menus, toolbars, inspector, backend status and log drawer."""

import os
import shutil
from datetime import datetime

import gi

gi.require_version("GdkPixbuf", "2.0")
gi.require_version("Gtk", "3.0")

from gi.repository import GdkPixbuf, Gio, Gtk, Pango  # noqa: E402

from ..adapters import ExifToolAdapter, ImageMagickAdapter  # noqa: E402
from .preview import PreviewPane  # noqa: E402

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
            ("Resize / Scale", "resize"),
            ("Calibration", "calibration"),
            ("Stacking", "stacking"),
            ("Image Geometry", "geometry"),
            ("Field Derotator", "derotator"),
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
            ("Sharpening / Unsharp", "unsharp"),
            ("Smoothing & Denoising", "filter"),
            ("Deconvolution", "deconvolution"),
            ("Star Reduction", "star-reduction"),
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
            ("FITS Header Inspector", "metadata"),
        ),
    ),
    (
        "Options",
        (
            ("Backend Settings", "settings"),
            ("Language", "language"),
        ),
    ),
)

TOOL_ITEMS = (
    ("document-open", "Open", "open"),
    ("document-save-as", "Export", "export"),
    ("dialog-information", "Metadata", "metadata"),
    ("zoom-in", "Zoom in", "zoom-in"),
    ("zoom-out", "Zoom out", "zoom-out"),
    ("zoom-fit-best", "Fit to window", "zoom-fit"),
    ("process-stop", "Cancel job", "cancel"),
)


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, app, registry, scratch, engine) -> None:
        super().__init__(application=app, title="Astro Studio")
        self.app = app
        self.registry = registry
        self.scratch = scratch
        self.engine = engine
        self.adapters = {
            "ImageMagick": ImageMagickAdapter(),
            "ExifTool": ExifToolAdapter(),
        }
        self.current_paths = []
        self.job_outputs = {}
        self.job_destinations = {}
        self.job_counter = 0
        self._reported_status = set()
        self.set_default_size(1100, 720)

        self.preview = PreviewPane()
        self.preview.set_size_request(640, 480)
        self.preview.connect("button-press-event", self._on_canvas_click)

        self._build_layout()
        self.on_backends_updated(registry)

    def _build_layout(self) -> None:
        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(root)

        root.pack_start(self._build_menu_bar(), False, False, 0)
        root.pack_start(self._build_toolbar(), False, False, 0)

        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned.set_position(740)

        left = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        frame = Gtk.Frame(label="Preview")
        scroll = Gtk.ScrolledWindow()
        scroll.add(self.preview)
        frame.add(scroll)
        left.pack_start(frame, True, True, 0)
        paned.pack1(left, True, False)

        right = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        right.set_border_width(6)
        right.pack_start(self._build_backend_panel(), False, False, 0)
        right.pack_start(self._build_inspector_panel(), False, False, 0)
        right.pack_start(self._build_log_panel(), True, True, 0)
        paned.pack2(right, False, True)
        root.pack_start(paned, True, True, 0)

        self.status_bar = Gtk.Statusbar()
        self.status_context = self.status_bar.get_context_id("astro-studio")
        self._status("Astro Studio ready")
        root.pack_start(self.status_bar, False, False, 0)

    def _build_menu_bar(self) -> Gtk.Widget:
        menu = Gio.Menu.new()
        for label, entries in MENU_LAYOUT:
            submenu = Gio.Menu.new()
            for item_label, action in entries:
                if item_label is None:
                    submenu.append_section(None, Gio.Menu.new())
                else:
                    submenu.append(item_label, "app." + action)
            menu.append_submenu(label, submenu)
        return Gtk.MenuBar.new_from_model(menu)

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

    def _build_backend_panel(self) -> Gtk.Widget:
        frame = Gtk.Frame(label="Backends (startup discovery)")
        self.backend_store = Gtk.ListStore(str, str, str)
        view = Gtk.TreeView(model=self.backend_store)
        for index, title in enumerate(("Name", "Status", "Version")):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=index)
            view.append_column(column)
        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(130)
        scroll.add(view)
        frame.add(scroll)
        return frame

    def _build_inspector_panel(self) -> Gtk.Widget:
        frame = Gtk.Frame(label="Parameter Inspector")
        grid = Gtk.Grid()
        grid.set_border_width(6)
        grid.set_row_spacing(4)
        grid.set_column_spacing(6)

        self.format_combo = Gtk.ComboBoxText()
        for extension in ("png", "jpg", "tif", "bmp"):
            self.format_combo.append_text(extension)
        self.format_combo.set_active(0)

        self.resize_entry = Gtk.Entry()
        self.resize_entry.set_placeholder_text("e.g. 50%")
        self.unsharp_entry = Gtk.Entry()
        self.unsharp_entry.set_placeholder_text("e.g. 1.5x1+0.7+0.02")
        self.crop_entry = Gtk.Entry()
        self.crop_entry.set_placeholder_text("e.g. 800x600+0+0")
        self.rotate_entry = Gtk.Entry()
        self.rotate_entry.set_placeholder_text("e.g. 90")

        fields = (
            ("Backend", Gtk.Label(label="ImageMagick (CLI)")),
            ("Format", self.format_combo),
            ("Resize", self.resize_entry),
            ("Unsharp", self.unsharp_entry),
            ("Crop", self.crop_entry),
            ("Rotate", self.rotate_entry),
        )
        for row, (label, widget) in enumerate(fields):
            grid.attach(Gtk.Label(label=label, xalign=0.0), 0, row, 1, 1)
            grid.attach(widget, 1, row, 1, 1)

        apply_button = Gtk.Button(label="Export via CLI")
        apply_button.connect("clicked", lambda *_: self._activate("export"))
        grid.attach(apply_button, 0, len(fields), 2, 1)
        frame.add(grid)
        return frame

    def _build_log_panel(self) -> Gtk.Widget:
        frame = Gtk.Frame(label="Terminal Drawer")
        self.log_buffer = Gtk.TextBuffer()
        view = Gtk.TextView(buffer=self.log_buffer)
        view.set_editable(False)
        view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        view.override_font(Pango.FontDescription("monospace 10"))
        scroll = Gtk.ScrolledWindow()
        scroll.add(view)
        frame.add(scroll)
        return frame

    def _activate(self, action: str) -> None:
        self.app.activate_action(action, None)

    def _status(self, text: str) -> None:
        self.status_bar.push(self.status_context, text)

    def _log(self, line: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        end = self.log_buffer.get_end_iter()
        self.log_buffer.insert(end, "[%s] %s\n" % (timestamp, line))

    def _on_canvas_click(self, widget, event) -> bool:
        position = self.preview.image_coordinates(event.x, event.y)
        if position:
            self._status("X=%d  Y=%d (preview readout)" % position)
        return False

    def on_backends_updated(self, registry) -> None:
        self.backend_store.clear()
        for spec in registry.specs:
            self.backend_store.append(registry.status[spec.name].label())
        available = sum(1 for status in registry.status.values() if status.available)
        self._status(
            "%d/%d backends installed | %d image(s) open"
            % (available, len(registry.status), len(self.current_paths))
        )
        self.app.update_action_sensitivity()

        for status in registry.status.values():
            key = (status.name, status.available, status.version)
            if key in self._reported_status:
                continue
            self._reported_status.add(key)
            if status.available:
                self._log("%s: available (version %s)" % (status.name, status.version or "unknown"))
            else:
                self._log("%s: not installed - related menu actions disabled" % status.name)

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
        image_filter.set_name("Images")
        for extension in ("jpg", "jpeg", "png", "tif", "tiff", "bmp", "fits", "fit", "cr2", "nef"):
            image_filter.add_pattern("*." + extension)
        dialog.add_filter(image_filter)
        if dialog.run() == Gtk.ResponseType.OK:
            for path in dialog.get_filenames():
                self._open_file(path)
        dialog.destroy()

    def _open_file(self, path: str) -> None:
        try:
            pixbuf = GdkPixbuf.Pixbuf.new_from_file(path)
        except Exception as exc:
            self._log("Cannot render %s: %s" % (path, exc))
            return
        self.current_paths.append(path)
        self.preview.set_pixbuf(pixbuf, path)
        self._status("Opened %s (%dx%d)" % (path, pixbuf.get_width(), pixbuf.get_height()))
        self._log("Loaded for display: %s" % path)

    def action_export(self) -> None:
        if not self.current_paths:
            self._log("Open at least one image before exporting")
            return
        adapter = self.adapters["ImageMagick"]
        if not self.registry.available(adapter.name):
            self._log("Backend unavailable: %s (install it to enable export)" % adapter.name)
            return

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
        source = self.current_paths[-1]
        dialog.set_current_name(
            "%s_processed.%s"
            % (os.path.splitext(os.path.basename(source))[0], self._target_format())
        )
        response = dialog.run()
        destination = dialog.get_filename() if response == Gtk.ResponseType.OK else None
        dialog.destroy()
        if not destination:
            return

        self.job_counter += 1
        job_id = "export-%d" % self.job_counter
        job_dir = self.scratch.job_dir(job_id)
        output = adapter.output_path(job_dir, source, self._target_format())
        params = {
            "crop": self.crop_entry.get_text() or None,
            "resize": self.resize_entry.get_text() or None,
            "rotate": self.rotate_entry.get_text() or None,
            "unsharp": self.unsharp_entry.get_text() or None,
        }
        argv = adapter.build_argv([source], output, params)
        self.job_outputs[job_id] = output
        self.job_destinations[job_id] = destination
        self._log("Dispatching CLI job %s: %s" % (job_id, " ".join(argv)))
        self._status("Running %s..." % adapter.name)
        self.engine.run(job_id, argv, on_log=self._log, on_done=self._on_export_done)
        self.app.update_action_sensitivity()

    def _target_format(self) -> str:
        return self.format_combo.get_active_text() or "png"

    def _on_export_done(self, result) -> None:
        output = self.job_outputs.pop(result.job_id, None)
        destination = self.job_destinations.pop(result.job_id, None)
        if not result.ok:
            self._log(
                "Job %s failed (exit %s): %s"
                % (result.job_id, result.exit_code, result.error or result.stderr)
            )
            self._status("CLI job failed")
        else:
            try:
                shutil.copyfile(output, destination)
                self.preview.load(output)
                self._log("Backend wrote %s; exported copy to %s" % (output, destination))
                self._status("Export complete: %s" % destination)
            except Exception as exc:
                self._log("Export copy failed: %s" % exc)
                self._status("Export failed")
        self.app.update_action_sensitivity()

    def action_metadata(self) -> None:
        if not self.current_paths:
            self._log("Open at least one image before reading metadata")
            return
        adapter = self.adapters["ExifTool"]
        if not self.registry.available(adapter.name):
            self._log("Backend unavailable: %s" % adapter.name)
            return
        self.job_counter += 1
        job_id = "metadata-%d" % self.job_counter
        argv = adapter.build_argv(self.current_paths)
        self._log("Dispatching CLI job %s: %s" % (job_id, " ".join(argv)))
        self.engine.run(job_id, argv, on_log=self._log, on_done=self._on_metadata_done)
        self.app.update_action_sensitivity()

    def _on_metadata_done(self, result) -> None:
        if not result.ok:
            self._log("Metadata job failed: %s" % (result.error or result.stderr))
        else:
            self.metadata_text = result.stdout
            self._log("Metadata received from %s (%d bytes)" % ("ExifTool", len(result.stdout)))
            self._show_metadata(result.stdout)
        self.app.update_action_sensitivity()

    def _show_metadata(self, text: str) -> None:
        dialog = Gtk.Dialog(title="FITS / EXIF metadata", parent=self, modal=True)
        dialog.add_button(Gtk.STOCK_CLOSE, Gtk.ResponseType.CLOSE)
        text_view = Gtk.TextView()
        text_view.set_editable(False)
        text_view.override_font(Pango.FontDescription("monospace 10"))
        buffer = text_view.get_buffer()
        buffer.set_text(text)
        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_size(560, 320)
        scroll.add(text_view)
        content = dialog.get_content_area()
        content.pack_start(scroll, True, True, 6)
        dialog.show_all()
        dialog.run()
        dialog.destroy()

    def action_cancel(self) -> None:
        jobs = self.engine.active_jobs
        for job_id in jobs:
            self.engine.cancel(job_id)
        if jobs:
            self._log("Cancelled jobs: %s" % ", ".join(jobs))
            self._status("Jobs cancelled")
        self.app.update_action_sensitivity()

    def action_close(self) -> None:
        if self.current_paths:
            self.current_paths.pop()
        self.preview.clear()
        self._status("Closed active view")

    def action_close_all(self) -> None:
        self.current_paths.clear()
        self.preview.clear()
        self._status("All views closed")

    def action_settings(self) -> None:
        self._log("Backend availability: %s" % "; ".join(self.registry.summary()))

    def action_undo(self) -> None:
        self._log("Undo applies to pipeline parameters; no changes recorded")

    def action_redo(self) -> None:
        self._log("Redo applies to pipeline parameters; no changes recorded")

    def action_resize(self) -> None:
        self.resize_entry.grab_focus()
        self._log("Set a resize flag, then use Export via CLI")

    def action_unsharp(self) -> None:
        self.unsharp_entry.grab_focus()
        self._log("Set an unsharp flag, then use Export via CLI")

    def action_zoom_in(self) -> None:
        self.preview.zoom_in()

    def action_zoom_out(self) -> None:
        self.preview.zoom_out()

    def action_zoom_fit(self) -> None:
        self.preview.zoom_fit()

    def action_quit(self) -> None:
        self.engine.cancel_all()
        self.scratch.cleanup_all()
        self.app.quit()
