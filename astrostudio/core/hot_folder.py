"""Poll a session folder and trigger a calibration + stacking plan on new lights."""

import os
from typing import Callable, Dict, List, Optional, Set, Tuple

from gi.repository import GLib

from .calibration import discover_calibration

PlanCallback = Callable[[List[str], Dict[str, List[str]]], None]


class HotFolderWatcher:
    """Small GLib timer that detects new light frames by path/size/mtime."""

    def __init__(
        self,
        root: str,
        on_new_lights: PlanCallback,
        interval_s: float = 5.0,
    ) -> None:
        self.root = root
        self.on_new_lights = on_new_lights
        self.interval_ms = max(1, int(interval_s * 1000))
        self.known: Set[str] = set()
        self.source_id: Optional[int] = None

    def snapshot(self) -> Tuple[Dict[str, List[str]], Set[str]]:
        found = discover_calibration(self.root)
        signatures = set()
        for paths in found.values():
            for path in paths:
                try:
                    stat = os.stat(path)
                    signatures.add("%s:%d:%d" % (path, stat.st_size, int(stat.st_mtime)))
                except OSError:
                    continue
        return found, signatures

    def poll(self) -> bool:
        found, signatures = self.snapshot()
        new = signatures - self.known
        if self.known and new and found.get("light"):
            self.on_new_lights(found["light"], found)
        self.known = signatures
        return True

    def start(self) -> None:
        if self.source_id is not None:
            return
        self.poll()
        self.source_id = GLib.timeout_add(self.interval_ms, self.poll)

    def stop(self) -> None:
        if self.source_id is not None:
            GLib.source_remove(self.source_id)
            self.source_id = None


def folders_from_files(found: Dict[str, List[str]]) -> Dict[str, str]:
    """Return one directory per calibration category for Siril scripts."""
    return {
        key: (os.path.dirname(paths[0]) if paths else "")
        for key, paths in found.items()
    }
