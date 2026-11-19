"""Append-only operational log shared across Astro Studio sessions."""

import json
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List


class OperationLog:
    """Record CLI jobs and GUI actions as newline-delimited JSON.

    The file lives under the XDG data directory and is never truncated, so
    timing data can be analysed across multiple sessions.
    """

    def __init__(self, path: str = None, session: str = None) -> None:
        if path:
            self.path = path
        else:
            data_home = os.environ.get("XDG_DATA_HOME") or os.path.join(
                os.path.expanduser("~"), ".local", "share"
            )
            self.path = os.path.join(data_home, "astro-studio", "operations.jsonl")
        self.session = session or uuid.uuid4().hex[:8]

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
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(entry, sort_keys=True) + "\n")
        return entry

    def entries(self) -> List[Dict[str, Any]]:
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                return [json.loads(line) for line in handle if line.strip()]
        except (OSError, ValueError):
            return []
