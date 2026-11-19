"""Dock panel listing CLI jobs with state and retry support."""

import gi

gi.require_version("Gtk", "3.0")

from gi.repository import Gtk  # noqa: E402


class JobPanel(Gtk.Box):
    def __init__(self, manager, on_retry) -> None:
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.manager = manager
        self.store = Gtk.ListStore(str, str, str, str)
        view = Gtk.TreeView(model=self.store)
        for index, title in enumerate(("Job", "State", "Seconds", "Command")):
            view.append_column(
                Gtk.TreeViewColumn(title, Gtk.CellRendererText(), text=index)
            )
        self.view = view
        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(70)
        scroll.add(view)
        retry = Gtk.Button(label="Retry selected")
        retry.connect("clicked", lambda *_: self._retry(on_retry))
        self.pack_start(scroll, True, True, 0)
        self.pack_start(retry, False, False, 0)

    def _retry(self, callback) -> None:
        selection = self.view.get_selection().get_selected()[1]
        if selection is None:
            return
        callback(self.store[selection][0])

    def refresh(self) -> None:
        self.store.clear()
        for job in self.manager.entries():
            self.store.append(
                (
                    job.job_id,
                    job.state,
                    "%.2f" % job.duration_s,
                    " ".join(job.argv),
                )
            )
