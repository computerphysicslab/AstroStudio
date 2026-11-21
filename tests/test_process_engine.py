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


def test_job_end_callback_sees_no_active_jobs():
    seen = []
    engine = ProcessEngine(on_job_end=lambda job_id, result: seen.append(engine.active_jobs))
    engine.run("echo-end", ["/bin/echo", "done"])
    _wait_for_callbacks()
    assert seen == [[]]


def test_user_cancel_escalates_to_sigkill(monkeypatch, tmp_path):
    import signal
    from types import SimpleNamespace

    log = OperationLog(str(tmp_path / "operations.jsonl"), session="cancel-kill")
    engine = ProcessEngine(operation_log=log, kill_grace_s=0.1)
    result = []
    handle = engine.run("sleep", ["/bin/sleep", "10"], on_done=result.append)
    assert engine.cancel("sleep")
    assert handle.kill_source is not None

    killed = []

    class FakeProcess:
        def send_signal(self, sig):
            killed.append(sig)

    fake = SimpleNamespace(
        finished=False,
        cancelled=True,
        process=FakeProcess(),
        cancellable=SimpleNamespace(cancel=lambda: None),
        error="cancelled by user",
        job_id="sleep",
        kill_source=None,
        process_finished=False,
    )
    monkeypatch.setattr(engine, "_maybe_finish", lambda _handle: None)
    engine._force_kill(fake)
    assert killed == [signal.SIGKILL]
    assert fake.error == "job killed after cancel"
    events = {entry["event"] for entry in log.entries()}
    assert "job_killed" in events


def test_job_timeout_escalates_and_reports(tmp_path):
    from astrostudio.core.operation_log import OperationLog

    log = OperationLog(str(tmp_path / "operations.jsonl"), session="timeout-test")
    engine = ProcessEngine(
        operation_log=log, job_timeout_s=0.2, kill_grace_s=0.1
    )
    results = []
    engine.run(
        "slow", ["/bin/sh", "-c", "trap '' TERM; sleep 10"], on_done=results.append
    )
    _wait_for_callbacks(5)
    assert len(results) == 1
    assert results[0].error is not None
    assert "timeout" in results[0].error or "killed" in results[0].error
    events = {entry["event"] for entry in log.entries()}
    assert "job_timeout" in events
    assert "job_killed" in events
