"""Astrometry adapter and artifact helper tests."""

import json

from astrostudio.adapters import SkyStackerAdapter
from astrostudio.core.astrometry import (
    find_output,
    find_plate_solution,
    summarize_solution,
)


def test_plate_solve_argv_uses_wcs_capable_image_op():
    adapter = SkyStackerAdapter()
    argv = adapter.build_plate_solve_argv(
        "/data/light.png", "/tmp/job", "83.82,-5.39", offline=True
    )
    assert argv == [
        "skystacker",
        "--process-image",
        "/data/light.png",
        "--image-op",
        "sky-map",
        "--image-output",
        "/tmp/job",
        "--no-donation",
        "--plate-solve",
        "--plate-center",
        "83.82,-5.39",
        "--gaia-offline",
    ]


def test_sky_map_and_cutout_argv_include_plate_solve():
    adapter = SkyStackerAdapter()
    sky_map = adapter.build_sky_map_argv("a.png", "/tmp/job", "10,20")
    assert sky_map[sky_map.index("--image-op") + 1] == "sky-map"
    assert "--plate-solve" in sky_map
    assert "--plate-center" in sky_map

    cutout = adapter.build_survey_cutout_argv("a.png", "/tmp/job", "Panstarrs1")
    assert "--survey-hips" in cutout
    assert "Panstarrs1" in cutout
    assert "--plate-solve" in cutout


def test_find_plate_solution_and_summarize(tmp_path):
    nested = tmp_path / "results"
    nested.mkdir()
    per_image = nested / "IMG_4062_plate_solution.json"
    per_image.write_text(
        json.dumps({"ra_center": 83.82, "dec_center": -5.39, "fov_deg": 1.4, "status": "ok"})
    )
    assert find_output(str(tmp_path), [".json"]) == str(per_image)
    assert find_plate_solution(str(tmp_path)) == str(per_image)

    canonical = nested / "plate_solution.json"
    canonical.write_text(per_image.read_text())
    assert find_plate_solution(str(tmp_path)) == str(canonical)

    summary = summarize_solution(str(canonical))
    assert "fov_deg: 1.4" in summary
    assert "ra_center: 83.82" in summary
    assert summary.index("fov_deg") < summary.index("status")
