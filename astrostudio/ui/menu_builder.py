"""Menu construction helpers for the GTK application."""

import os

from gi.repository import Gio, Gtk  # noqa: E402


def toggle_label(action: str, label: str, visible: bool) -> str:
    state = "On" if visible else "Off"
    return "%s: %s" % (label, state)


def append_menu_items(menu: Gio.Menu, items, registry: dict = None, tr=None) -> None:
    translate = tr or (lambda text: text)
    for item in items:
        if item[0] is None:
            continue
        if len(item) == 3:
            submenu = Gio.Menu.new()
            append_menu_items(submenu, item[2], registry, tr)
            menu.append_submenu(translate(item[0]), submenu)
        else:
            label = item[0]
            if registry is not None:
                label = registry(item[1], translate(item[0]))
            menu.append(label, "app." + item[1])


class MenuBuilder:
    """Builds both the Gio menu bar model and manual right-click GTK menus."""

    def __init__(self, window, layout, toggle_panels, panel_for_action) -> None:
        self.window = window
        self.layout = layout
        self.toggle_panels = toggle_panels
        self.panel_for_action = panel_for_action

    def dynamic_entries(self, entries):
        result = []
        for item in entries:
            if item[0] is None:
                result.append(item)
            elif len(item) == 3:
                result.append(
                    (item[0], None, self.dynamic_entries(item[2]))
                )
            elif item[1] in self.toggle_panels:
                panel = self.panel_for_action(item[1])
                visible = panel.get_visible() if panel is not None else True
                result.append(
                    (
                        toggle_label(
                            item[1],
                            self.window.translator.tr(self.toggle_panels[item[1]]),
                            visible,
                        ),
                        item[1],
                    )
                )
            else:
                result.append(item)
        return result

    def entries_with_recent(self, entries):
        paths = self.window.settings.get("recent_images", [])[:10]
        if paths:
            recent = [
                (os.path.basename(path), "open-recent-%d" % index)
                for index, path in enumerate(paths)
            ]
        else:
            recent = [(self.window.translator.tr("No recent images"), "open")]
        dynamic = list(entries)
        return [
            dynamic[0],
            (self.window.translator.tr("Open Recent"), None, tuple(recent)),
        ] + dynamic[1:]

    def build_menu_model(self) -> Gio.Menu:
        menu = Gio.Menu.new()
        for label, entries in self.layout:
            submenu = Gio.Menu.new()
            dynamic = self.dynamic_entries(entries)
            if label == "File":
                first, remaining = dynamic[:1], dynamic[1:]
                append_menu_items(submenu, first, None, self.window.translator.tr)
                recent_menu = Gio.Menu.new()
                paths = self.window.settings.get("recent_images", [])
                if paths:
                    for index, path in enumerate(paths[:10]):
                        recent_menu.append(
                            os.path.basename(path), "app.open-recent-%d" % index
                        )
                else:
                    recent_menu.append(
                        self.window.translator.tr("No recent images"), "app.open"
                    )
                submenu.append_submenu(
                    self.window.translator.tr("Open Recent"), recent_menu
                )
                append_menu_items(
                    submenu, remaining, None, self.window.translator.tr
                )
            else:
                append_menu_items(
                    submenu, dynamic, None, self.window.translator.tr
                )
            menu.append_submenu(self.window.translator.tr(label), submenu)
        return menu

    def build_popup_menu(self, items) -> Gtk.Menu:
        popup = Gtk.Menu()
        for item in items:
            if item[0] is None:
                popup.append(Gtk.SeparatorMenuItem())
            elif len(item) == 3:
                parent = Gtk.MenuItem(label=self.window.translator.tr(item[0]))
                parent.set_submenu(self.build_popup_menu(item[2]))
                popup.append(parent)
            else:
                entry = Gtk.MenuItem(label=self.window.translator.tr(item[0]))
                entry.connect(
                    "activate",
                    lambda *_widget, name=item[1]: self.window.actions.invoke(name),
                )
                popup.append(entry)
        return popup

    def build_app_popup(self) -> Gtk.Menu:
        popup = Gtk.Menu()
        for label, entries in self.layout:
            dynamic = self.dynamic_entries(entries)
            if label == "File":
                dynamic = self.entries_with_recent(dynamic)
            parent = Gtk.MenuItem(label=self.window.translator.tr(label))
            parent.set_submenu(self.build_popup_menu(dynamic))
            popup.append(parent)
        return popup
