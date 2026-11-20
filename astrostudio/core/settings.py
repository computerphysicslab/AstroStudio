"""Persistent user preferences for Astro Studio."""

import copy
import json
import os
from typing import Any, Dict, Optional

DEFAULTS: Dict[str, Any] = {
    "language": "en",
    "theme": "system",
    "offline": False,
    "threads": 0,
    "job_timeout_s": 1800,
    "history_depth": 10,
    "remote_mode": "ssh",
    "remote_target": "",
    "font_size": 9,
    "accent_color": "green",
    "show_thumbnails": False,
    "show_resources": True,
    "recent_transforms": [],
    "binary_overrides": {},
    "scratch_dir": "",
    "cache_dir": "",
    "gaia_nside": 64,
    "linear_override": False,
    "blind_catalog_dir": "",
    "blind_catalog": "mag07",
    "offline_catalogs": ["mag07"],
    "survey_hips": "CDS/P/DSS2/color",
    "recent_images": [],
    "shortcuts": {},
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
        self.data: Dict[str, Any] = copy.deepcopy(DEFAULTS)
        self.load()

    def load(self) -> None:
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                loaded = json.load(handle)
            if isinstance(loaded, dict):
                self.data.update(loaded)
                for key in ("enabled_backends", "binary_overrides", "shortcuts"):
                    if not isinstance(self.data.get(key), dict):
                        self.data[key] = {}
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
