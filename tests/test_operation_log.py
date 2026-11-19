"""Persistent operation log tests."""

from astrostudio.core.operation_log import OperationLog


def test_entries_append_across_sessions(tmp_path):
    path = str(tmp_path / "operations.jsonl")
    first = OperationLog(path, session="a")
    first.record("session_start", application="astro-studio")
    first.record("cli_end", job_id="j1", duration_s=1.25, exit_code=0)

    second = OperationLog(path, session="b")
    second.record("session_start", application="astro-studio")

    entries = second.entries()
    assert [entry["event"] for entry in entries] == [
        "session_start",
        "cli_end",
        "session_start",
    ]
    assert [entry["session"] for entry in entries] == ["a", "a", "b"]
    assert entries[1]["duration_s"] == 1.25
    assert "timestamp" in entries[0]


def test_log_rotates_when_size_exceeded(tmp_path):
    path = str(tmp_path / "ops.jsonl")
    log = OperationLog(path, session="s", max_bytes=120, backups=2)
    for index in range(12):
        log.record("event", index=index, payload="x" * 20)
    assert (tmp_path / "ops.jsonl").exists()
    assert (tmp_path / "ops.jsonl.1").exists()
    assert len(log.entries()) < 12
