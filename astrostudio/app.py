"""Gtk.Application bootstrap and action routing."""

import sys

import gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gio, GLib, Gtk  # noqa: E402

from .core import BackendRegistry, ProcessEngine, ScratchManager  # noqa: E402
from .ui import MainWindow  # noqa: E402
from .ui.main_window import MENU_LAYOUT  # noqa: E402

ACTION_NAMES = frozenset(
    {action for _label, entries in MENU_LAYOUT for _item, action in entries if action}
    | {"cancel"}
)


class AstroStudioApplication(Gtk.Application):
    def __init__(self) -> None:
        super().__init__(
            application_id="org.astrostudio.gui",
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )
        self.registry = BackendRegistry()
        self.scratch = ScratchManager()
        self.engine = ProcessEngine()
        self.window = None

        for name in ACTION_NAMES:
            action = Gio.SimpleAction.new(name, None)
            action.connect("activate", self._on_action, name)
            self.add_action(action)

        self.set_accels_for_action("app.open", ["<Control>o"])
        self.set_accels_for_action("app.export", ["<Control><Shift>s"])
        self.set_accels_for_action("app.metadata", ["<Control>i"])
        self.set_accels_for_action("app.quit", ["<Control>q"])

    def _on_action(self, _action, _parameter, name: str) -> None:
        if self.window is None:
            return
        handler = getattr(self.window, "action_" + name.replace("-", "_"), None)
        if handler:
            handler()
        else:
            self.window._log("Action pending CLI adapter: %s" % name)

    def do_activate(self) -> None:
        if self.window is None:
            self.window = MainWindow(self, self.registry, self.scratch, self.engine)
            self.window.show_all()
            self.window.present()
            self.update_action_sensitivity()
            GLib.idle_add(self._discover_backends)

    def _discover_backends(self) -> bool:
        self.registry.probe(self.engine, on_update=self._backends_updated)
        return False

    def _backends_updated(self, registry: BackendRegistry) -> None:
        if self.window is not None:
            self.window.on_backends_updated(registry)

    def update_action_sensitivity(self) -> None:
        for name in ACTION_NAMES:
            action = self.lookup_action(name)
            if action is not None:
                action.set_enabled(self.registry.is_action_enabled(name))
        cancel_action = self.lookup_action("cancel")
        if cancel_action is not None:
            cancel_action.set_enabled(bool(self.engine.active_jobs))

    def do_shutdown(self) -> None:
        self.engine.cancel_all()
        self.scratch.cleanup_all()
        Gtk.Application.do_shutdown(self)


def main() -> int:
    return AstroStudioApplication().run(sys.argv)
