"""Asynchronous process engine tests."""

from gi.repository import GLib

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


def test_successful_job_captures_stdout():
    results = []
    engine = ProcessEngine()
    engine.run("echo", ["/bin/echo", "hello backend"], on_done=results.append)
    _wait_for_callbacks()
    assert len(results) == 1
    assert results[0].ok
    assert "hello backend" in results[0].stdout
    assert results[0].exit_code == 0
