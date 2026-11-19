"""Persistent user preferences for Astro Studio."""

import json
import os
from typing import Any, Dict, Optional

DEFAULTS: Dict[str, Any] = {
    "language": "en",
    "theme": "system",
    "offline": False,
    "threads": 0,
    "enabled_backends": {},
}


class SettingsManager:
    """Load and save preferences under the XDG config directory."""

    def __init__(self, path: str = None) -> None:
        if path:
            self.path = path
        else:
            config_home = os.environ.get("XDG_CONFIG_HOME") or os.path.join(
                os.path.expanduser("~"), ".config"
            )
            self.path = os.path.join(config_home, "astro-studio", "settings.json")
        self.data: Dict[str, Any] = dict(DEFAULTS)
        self.load()

    def load(self) -> None:
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                loaded = json.load(handle)
            if isinstance(loaded, dict):
                self.data.update(loaded)
                if not isinstance(self.data.get("enabled_backends"), dict):
                    self.data["enabled_backends"] = {}
        except (OSError, ValueError):
            pass

    def save(self) -> None:
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(self.path, "w", encoding="utf-8") as handle:
            json.dump(self.data, handle, indent=2, sort_keys=True)
            handle.write("\n")

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    def is_backend_enabled(self, name: str) -> bool:
        return bool(self.data["enabled_backends"].get(name, True))

    def set_backend_enabled(self, name: str, enabled: bool) -> None:
        self.data["enabled_backends"][name] = bool(enabled)
