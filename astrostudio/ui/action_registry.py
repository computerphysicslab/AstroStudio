"""Action dispatch registry shared by the menu bar, popups and accelerators."""

import re


class ActionRegistry:
    """Resolves action names to MainWindow handler methods."""

    def __init__(self, window) -> None:
        self.window = window

    @staticmethod
    def method_name(action: str) -> str:
        return "action_" + re.sub(r"[^\w]", "_", action)

    def invoke(self, action: str) -> bool:
        handler = getattr(self.window, self.method_name(action), None)
        if handler is None:
            return False
        handler()
        return True

    def activate(self, action: str) -> None:
        gio_action = self.window.app.lookup_action(action)
        if gio_action is not None and not gio_action.get_enabled():
            self.window._log("Action unavailable: %s (check Backends panel)" % action)
            self.window._status(
                "%s: %s" % (self.window.translator.tr("Action unavailable"), action)
            )
            return
        if not self.invoke(action):
            self.window.app.activate_action(action, None)
