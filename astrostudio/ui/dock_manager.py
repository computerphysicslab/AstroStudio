"""Right-dock panel construction and visibility management."""

from gi.repository import Gtk, Pango


PANEL_ATTRS = {
    "toggle-backends": "backends_panel",
    "toggle-histogram": "histogram_panel",
    "toggle-terminal": "terminal_panel",
    "toggle-resources": "resources_panel",
    "toggle-jobs": "job_panel",
}


class DockManager:
    """Owns close buttons and On/Off toggles for docked panels."""

    def __init__(self, window) -> None:
        self.window = window

    def panel_with_close(self, title: str, content: Gtk.Widget) -> Gtk.Widget:
        panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        header.set_size_request(-1, 16)
        label = Gtk.Label(label=self.window.translator.tr(title), xalign=0.0)
        self.window.panel_labels[title] = label
        label.set_hexpand(True)
        label.set_margin_top(0)
        label.set_margin_bottom(0)
        label.override_font(Pango.FontDescription("sans 9"))
        close_button = Gtk.Button.new_from_icon_name(
            "window-close-symbolic", Gtk.IconSize.MENU
        )
        close_button.set_relief(Gtk.ReliefStyle.NONE)
        close_button.set_tooltip_text("Hide panel")
        close_button.connect("clicked", lambda *_: self.window._on_panel_closed(panel))
        header.pack_start(label, True, True, 0)
        header.pack_start(close_button, False, False, 0)
        panel.pack_start(header, False, False, 0)
        panel.pack_start(content, True, True, 0)
        return panel

    def panel_for_action(self, action: str):
        return getattr(self.window, PANEL_ATTRS[action], None)

    def toggle(self, action: str) -> None:
        panel = self.panel_for_action(action)
        if panel is None:
            return
        panel.set_visible(not panel.get_visible())
        if action == "toggle-terminal" and panel.get_visible():
            self.window.log_view.scroll_to_iter(
                self.window.log_buffer.get_end_iter(), 0.0, False, 0.0, 0.0
            )
        self.window._update_toggle_labels()

    def update_labels(self) -> None:
        self.window._rebuild_menu_bar()
