"""Pipeline script export tests."""

from astrostudio.core.pipeline_export import cli_entries, write_makefile, write_shell


ENTRIES = [
    {"event": "cli_start", "session": "a", "argv": ["convert", "in.png", "out.tif"]},
    {"event": "cli_end", "session": "a", "argv": ["convert", "in.png", "out.tif"]},
    {"event": "cli_start", "session": "b", "argv": ["echo", "other"]},
    {"event": "cli_start", "session": "a", "argv": ["convert", "--resize", "50%", "a b.tif", "c.tif"]},
]


def test_cli_entries_filters_by_session():
    jobs = cli_entries(ENTRIES, "a")
    assert len(jobs) == 2
    assert jobs[0][0] == "convert"


def test_shell_and_makefile_quote_paths(tmp_path):
    jobs = cli_entries(ENTRIES, "a")
    shell = tmp_path / "pipeline.sh"
    make = tmp_path / "pipeline.mk"
    write_shell(jobs, str(shell))
    write_makefile(jobs, str(make))
    shell_text = shell.read_text()
    assert "set -euo pipefail" in shell_text
    assert "'a b.tif'" in shell_text
    make_text = make.read_text()
    assert "SHELL := /bin/bash" in make_text
    assert "job-000" in make_text
