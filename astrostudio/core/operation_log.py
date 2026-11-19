"""Append-only operational log shared across Astro Studio sessions."""

import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List


class OperationLog:
    """Record CLI jobs and GUI actions as newline-delimited JSON.

    Rotates the file by size, keeping older JSONL files as ``.1``, ``.2`` etc.
    Timing data therefore survives multiple sessions with bounded disk usage.
    """

    def __init__(
        self,
        path: str = None,
        session: str = None,
        max_bytes: int = 20 * 1024 * 1024,
        backups: int = 3,
    ) -> None:
        if path:
            self.path = path
        else:
            data_home = os.environ.get("XDG_DATA_HOME") or os.path.join(
                os.path.expanduser("~"), ".local", "share"
            )
            self.path = os.path.join(data_home, "astro-studio", "operations.jsonl")
        self.session = session or uuid.uuid4().hex[:8]
        self.max_bytes = max_bytes
        self.backups = backups

    def record(self, event: str, **fields: Any) -> Dict[str, Any]:
        entry: Dict[str, Any] = {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "session": self.session,
            "event": event,
        }
        entry.update(fields)
        directory = os.path.dirname(self.path)
        if directory:
            os.makedirs(directory, exist_ok=True)
        self._rotate_if_needed()
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")
        return entry

    def _rotate_if_needed(self) -> None:
        try:
            if os.path.getsize(self.path) < self.max_bytes:
                return
        except OSError:
            return
        for index in range(self.backups, 0, -1):
            source = self.path if index == 1 else "%s.%d" % (self.path, index - 1)
            target = "%s.%d" % (self.path, index)
            if os.path.exists(source):
                os.replace(source, target)

    def entries(self) -> List[Dict[str, Any]]:
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                return [json.loads(line) for line in handle if line.strip()]
        except (OSError, ValueError):
            return []
