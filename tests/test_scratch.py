"""Scratch-space isolation tests."""

from pathlib import Path

from astrostudio.core.scratch import ScratchManager


def test_scratch_job_directory_and_cleanup(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path / "runtime"))
    (tmp_path / "runtime").mkdir()
    source = tmp_path / "original.fits"
    source.write_bytes(b"original data")

    scratch = ScratchManager("session-1")
    job_dir = Path(scratch.job_dir("export 1"))
    assert job_dir.is_dir()
    output = job_dir / "result.png"
    output.write_bytes(b"backend output")

    scratch.cleanup_all()
    assert not output.exists()
    assert source.read_bytes() == b"original data"
