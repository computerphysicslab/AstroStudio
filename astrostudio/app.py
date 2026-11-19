"""Gtk.Application bootstrap and action routing."""

import os
import sys
from typing import List, Sequence

import gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gio, GLib, Gtk  # noqa: E402

from .core import (  # noqa: E402
    BackendRegistry,
    Estimator,
    OperationLog,
    ProcessEngine,
    ScratchManager,
    SettingsManager,
)
from .ui import MainWindow  # noqa: E402
from .ui.main_window import MENU_LAYOUT  # noqa: E402

def _iter_actions(entries):
    for item in entries:
        if item[0] is None:
            continue
        if len(item) == 3:
            for action in _iter_actions(item[2]):
                yield action
        else:
            yield item[1]


def iter_menu_actions():
    for _label, entries in MENU_LAYOUT:
        for action in _iter_actions(entries):
            yield action


ACTION_NAMES = frozenset(set(iter_menu_actions()) | {"cancel"})


def paths_from_command_line(command_line) -> List[str]:
    """Extract image paths from a Gio command line (file manager "Open With")."""
    paths: List[str] = []
    try:
        files = command_line.get_files()
        for gfile in files:
            path = gfile.get_path()
            if path and os.path.isfile(path) and path not in paths:
                paths.append(path)
    except Exception:
        pass
    try:
        arguments: Sequence[str] = command_line.get_arguments()
        for argument in arguments[1:]:
            if argument.startswith("-"):
                continue
            path = os.path.abspath(argument)
            if os.path.isfile(path) and path not in paths:
                paths.append(path)
    except Exception:
        pass
    return paths


class AstroStudioApplication(Gtk.Application):
    def __init__(self) -> None:
        super().__init__(
            application_id="org.astrostudio.gui.v2",
            flags=Gio.ApplicationFlags.HANDLES_OPEN,
        )
        self.settings = SettingsManager()
        self.registry = BackendRegistry(settings=self.settings)
        self.scratch = ScratchManager()
        self.operation_log = OperationLog()
        self.estimator = Estimator()
        self.operation_log.record("session_start", application="astro-studio")
        self.engine = ProcessEngine(operation_log=self.operation_log)
        self.window = None
        self.pending_paths: List[str] = []

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

    def do_open(self, files, n_files: int, hint: str) -> None:
        for gfile in files:
            path = gfile.get_path()
            if path and os.path.isfile(path) and path not in self.pending_paths:
                self.pending_paths.append(path)
        self.activate()

    def do_command_line(self, command_line) -> int:
        self.pending_paths.extend(paths_from_command_line(command_line))
        self.activate()
        return 0

    def do_activate(self) -> None:
        if self.window is None:
            self.window = MainWindow(self, self.registry, self.scratch, self.engine)
            self.window.show_all()
            self.update_action_sensitivity()
            GLib.idle_add(self._discover_backends)
        for path in self.pending_paths:
            self.window._open_file(path)
        self.pending_paths.clear()
        self.window.present()

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
        if self.window is not None and self.window.current_images:
            image = self.window.current_images[-1]
            history = (
                ("undo", self.window.workspace.can_undo(image)),
                ("redo", self.window.workspace.can_redo(image)),
            )
        else:
            history = (("undo", False), ("redo", False))
        for name, enabled in history:
            action = self.lookup_action(name)
            if action is not None:
                action.set_enabled(enabled)
        cancel = self.lookup_action("cancel")
        if cancel is not None:
            cancel.set_enabled(bool(self.engine.active_jobs))

    def do_shutdown(self) -> None:
        if self.window is not None:
            self.window._stop_progress()
        self.engine.cancel_all()
        self.scratch.cleanup_all()
        Gtk.Application.do_shutdown(self)


def main() -> int:
    return AstroStudioApplication().run(sys.argv)
