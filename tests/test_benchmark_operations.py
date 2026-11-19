"""Opt-in benchmark wrapper (never runs in the normal unit-test suite)."""

import os

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("ASTROSTUDIO_BENCHMARK") != "1",
    reason="set ASTROSTUDIO_BENCHMARK=1 to run the CLI benchmark",
)


def test_benchmark_appends_operation_log_entries():
    from benchmark_operations import run_benchmark

    entries = run_benchmark()
    assert any(entry["event"] == "benchmark_start" for entry in entries)
    assert any(entry["event"] == "benchmark_end" for entry in entries)
    assert any(
        entry["event"] == "benchmark_case" and entry["stage"] == "open"
        for entry in entries
    )
