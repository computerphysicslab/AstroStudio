"""Asynchronous process engine tests."""

from gi.repository import GLib

from astrostudio.core.operation_log import OperationLog
from astrostudio.core.process_engine import ProcessEngine


def _wait_for_callbacks(seconds=5):
    loop = GLib.MainLoop()
    GLib.timeout_add(seconds * 1000, loop.quit)
    loop.run()


def test_missing_binary_is_reported_without_crash():
    results = []
    engine = ProcessEngine()
    engine.run("missing", ["/definitely/not/a/real/binary"], on_done=results.append)
    _wait_for_callbacks()
    assert len(results) == 1
    assert results[0].job_id == "missing"
    assert results[0].error is not None
    assert not results[0].ok


def test_engine_records_job_timing_in_operation_log(tmp_path):
    log = OperationLog(str(tmp_path / "operations.jsonl"), session="test")
    engine = ProcessEngine(operation_log=log)
    done = []
    engine.run("echo-log", ["/bin/echo", "timed"], on_done=done.append)
    _wait_for_callbacks()

    assert len(done) == 1
    events = [(entry["event"], entry.get("job_id")) for entry in log.entries()]
    assert ("cli_start", "echo-log") in events
    assert ("cli_end", "echo-log") in events
    end = [entry for entry in log.entries() if entry["event"] == "cli_end"][0]
    assert end["exit_code"] == 0
    assert end["duration_s"] >= 0


def test_successful_job_captures_stdout():
    results = []
    engine = ProcessEngine()
    engine.run("echo", ["/bin/echo", "hello backend"], on_done=results.append)
    _wait_for_callbacks()
    assert len(results) == 1
    assert results[0].ok
    assert "hello backend" in results[0].stdout
    assert results[0].exit_code == 0


def test_cancel_reports_cancelled_state():
    engine = ProcessEngine()
    results = []
    handle = engine.run("sleep", ["/bin/sleep", "10"], on_done=results.append)
    assert engine.cancel("sleep")
    _wait_for_callbacks()
    assert len(results) == 1
    assert results[0].error == "cancelled by user"
    assert handle.finished
