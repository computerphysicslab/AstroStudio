"""Structured logging tests."""

from astrostudio.core.operation_log import OperationLog
from astrostudio.core.structured_log import StructuredLogger


def test_structured_logger_mirrors_to_sink_and_operation_log(tmp_path):
    log = OperationLog(str(tmp_path / "operations.jsonl"), session="log-test")
    messages = []
    logger = StructuredLogger(log, sink=lambda m, l, f: messages.append((m, l, f)))
    logger.info("opened image", action="open")
    logger.warning("slow job", seconds=12)

    assert messages == [
        ("opened image", "info", {"action": "open"}),
        ("slow job", "warning", {"seconds": 12}),
    ]
    entries = log.entries()
    assert len(entries) == 2
    assert entries[0]["event"] == "log"
    assert entries[0]["message"] == "opened image"
    assert entries[0]["action"] == "open"
    assert entries[1]["level"] == "warning"
    logger.close()
