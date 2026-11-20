"""Structured Python logging mirrored into the terminal and operation log."""

import logging
import uuid
from typing import Any, Callable, Dict, Optional

Sink = Callable[[str, str, Dict[str, Any]], None]


class CallbackHandler(logging.Handler):
    def __init__(self, callback: Sink) -> None:
        super().__init__()
        self.callback = callback

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.callback(
                record.getMessage(),
                record.levelname.lower(),
                getattr(record, "astro_fields", {}),
            )
        except Exception:
            self.handleError(record)


class StructuredLogger:
    """Route Python log records to a GUI sink and the persistent JSONL log."""

    def __init__(
        self,
        operation_log: Any = None,
        sink: Sink = None,
        namespace: str = None,
    ) -> None:
        self.operation_log = operation_log
        self.sink = sink
        self.name = namespace or ("astrostudio.%s" % uuid.uuid4().hex[:8])
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False
        self.handler = CallbackHandler(self._emit)
        self.logger.addHandler(self.handler)

    def _emit(self, message: str, level: str, fields: Dict[str, Any]) -> None:
        if self.operation_log is not None:
            self.operation_log.record("log", level=level, message=message, **fields)
        if self.sink is not None:
            self.sink(message, level, fields)

    def log(
        self,
        message: str,
        level: int = logging.INFO,
        **fields: Any,
    ) -> None:
        extra: Dict[str, Any] = {"astro_fields": fields} if fields else {}
        self.logger.log(level, message, extra=extra)

    def info(self, message: str, **fields: Any) -> None:
        self.log(message, logging.INFO, **fields)

    def warning(self, message: str, **fields: Any) -> None:
        self.log(message, logging.WARNING, **fields)

    def error(self, message: str, **fields: Any) -> None:
        self.log(message, logging.ERROR, **fields)

    def close(self) -> None:
        self.logger.removeHandler(self.handler)
        self.handler.close()
