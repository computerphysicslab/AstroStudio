"""Job manager state tests."""

from astrostudio.core.job_manager import JobManager
from astrostudio.core.process_engine import JobResult


def test_tracks_job_lifecycle_and_retry_argv():
    manager = JobManager()
    manager.start("j1", ["convert", "a.tiff", "b.tiff"])
    assert manager.entries()[0].state == "running"
    manager.finish("j1", JobResult(job_id="j1", argv=[], exit_code=0))
    assert manager.entries()[0].state == "done"
    assert manager.argv_for("j1") == ["convert", "a.tiff", "b.tiff"]
