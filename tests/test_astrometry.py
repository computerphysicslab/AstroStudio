"""Astrometry adapter and artifact helper tests."""

import json

from pathlib import Path

from astrostudio.adapters import SkyStackerAdapter
from astrostudio.core.astrometry import find_output, summarize_solution


def test_plate_solve_argv_includes_seed_and_cache_flags():
    adapter = SkyStackerAdapter()
    argv = adapter.build_plate_solve_argv(
        "/data/light.png", "/tmp/job", "83.82,-5.39", offline=True
    )
    assert argv == [
        "skystacker",
        "--process-image",
        "/data/light.png",
        "--image-op",
        "measure-quality",
        "--image-output",
        "/tmp/job",
        "--no-donation",
        "--plate-solve",
        "--json-report",
        "--plate-center",
        "83.82,-5.39",
        "--gaia-offline",
    ]


def test_sky_map_and_cutout_argv():
    adapter = SkyStackerAdapter()
    sky_map = adapter.build_sky_map_argv("a.png", "/tmp/job")
    assert "--image-op" in sky_map
    assert sky_map[sky_map.index("--image-op") + 1] == "sky-map"
    cutout = adapter.build_survey_cutout_argv("a.png", "/tmp/job", "Panstarrs1")
    assert "--survey-hips" in cutout
    assert "Panstarrs1" in cutout


def test_find_output_and_summarize_solution(tmp_path):
    nested = tmp_path / "results"
    nested.mkdir()
    solution = nested / "plate_solution.json"
    solution.write_text(
        json.dumps({"ra_center": 83.82, "dec_center": -5.39, "fov_deg": 1.4, "status": "ok"})
    )
    assert find_output(str(tmp_path), [".json"]) == str(solution)

    summary = summarize_solution(str(solution))
    assert "fov_deg: 1.4" in summary
    assert "ra_center: 83.82" in summary
    assert summary.index("fov_deg") < summary.index("status")
