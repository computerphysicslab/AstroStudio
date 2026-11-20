"""Reusable GTK dialog builders for parameter prompts."""

from gi.repository import Gtk

from .window_utils import make_draggable


class DialogFactory:
    """Creates draggable, consistently styled dialogs."""

    def __init__(self, parent) -> None:
        self.parent = parent

    def header(self, dialog: Gtk.Dialog, title: str) -> Gtk.HeaderBar:
        header = Gtk.HeaderBar()
        header.set_title(self.parent.translator.tr(title))
        header.set_show_close_button(True)
        dialog.set_titlebar(header)
        make_draggable(dialog, header)
        return header

    def ask_text(self, title: str, default: str = "") -> str:
        dialog = Gtk.Dialog(
            title=title,
            parent=self.parent,
            modal=True,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_OK, Gtk.ResponseType.OK,
            ),
        )
        self.header(dialog, title)
        entry = Gtk.Entry()
        entry.set_text(default)
        dialog.get_content_area().pack_start(entry, True, True, 6)
        dialog.show_all()
        response = dialog.run()
        value = entry.get_text() if response == Gtk.ResponseType.OK else None
        dialog.destroy()
        return value
