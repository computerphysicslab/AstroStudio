"""Astrometry adapter, solution parsing and artifact helper tests."""

import json
import math

from astrostudio.adapters import SkyStackerAdapter
from astrostudio.core.astrometry import (
    find_output,
    find_plate_solution,
    classify_backend_failure,
    sky_map_source_count,
    strip_svg_titles,
    summarize_solution,
)
from astrostudio.core.plate_solution import load_solution


def test_cr2_raw_import_argv_uses_skystacker_native_decoder():
    argv = SkyStackerAdapter().build_raw_import_argv("/tmp/in", "/tmp/out")
    assert argv == [
        "skystacker",
        "/tmp/in",
        "--output",
        "/tmp/out",
        "--overwrite",
        "--tiff",
        "--no-postprocess",
        "--no-register",
        "--workers",
        "2",
        "--no-donation",
    ]


def test_plate_solve_argv_uses_documented_image_op():
    argv = SkyStackerAdapter().build_plate_solve_argv(
        "/data/light.png",
        "/tmp/job",
        plate_center="83.822,-5.391",
        solver="gaia",
        offline=True,
        timeout=90,
        focal_length="50",
        pixel_size="4.3",
    )
    assert argv == [
        "skystacker",
        "--process-image",
        "/data/light.png",
        "--image-op",
        "plate-solve",
        "--image-output",
        "/tmp/job",
        "--no-donation",
        "--plate-solver",
        "gaia",
        "--astrometry-timeout",
        "90",
        "--gaia-nside",
        "64",
        "--plate-center",
        "83.822,-5.391",
        "--gaia-offline",
        "--solver-focal-length",
        "50",
        "--solver-pixel-size",
        "4.3",
    ]


def test_blind_solve_argv_uses_native_catalog_and_env_wrapper():
    adapter = SkyStackerAdapter()
    adapter.catalog_dir = "/tmp/catalogs"
    argv = adapter.build_blind_solve_argv(
        "photo.jpg", "/tmp/out", catalog="mag07", focal_length="50", pixel_size="4.3"
    )
    assert argv[:2] == ["/usr/bin/env", "SKYSTACKER_CATALOGS=/tmp/catalogs"]
    assert argv[2] == "skystacker"
    assert argv[argv.index("--image-op") + 1] == "plate-solve"
    assert argv[argv.index("--plate-solver") + 1] == "native"
    assert argv[argv.index("--blind-catalog") + 1] == "mag07"
    assert "--solver-focal-length" in argv


def test_sky_map_argv_requests_solve_and_uses_layered_product():
    argv = SkyStackerAdapter().build_sky_map_argv("a.png", "/tmp/job")
    assert argv[argv.index("--image-op") + 1] == "sky-map"
    assert "--plate-solve" in argv
    assert "--plate-solver" in argv


def test_classify_backend_failure_returns_actionable_hints():
    category, title, hint = classify_backend_failure("skystacker: hips2fits HTTP 404")
    assert category == "hips-service"
    assert title == "HiPS survey service unavailable"
    assert "CDS HiPS" in hint
    category, title, hint = classify_backend_failure(
        "plate solve: no consistent transform (0 matched pairs)"
    )
    assert category == "solver-matching"
    assert title == "Star matching failed"
    assert "astrometry.net" in hint
    assert classify_backend_failure("no catalog manifest found")[0] == "catalog-env"
    assert classify_backend_failure("something unexpected")[0] == "backend-error"


def test_sky_map_source_count_detects_empty_maps(tmp_path):
    populated = tmp_path / "map.svg"
    populated.write_text(
        '<svg><circle cx="1" cy="2" r="3"/><circle cx="4" cy="5" r="3"/></svg>',
        encoding="utf-8",
    )
    empty = tmp_path / "empty.svg"
    empty.write_text('<svg><g id="gaia-stars"></g></svg>', encoding="utf-8")
    assert sky_map_source_count(str(populated)) == 2
    assert sky_map_source_count(str(empty)) == 0
    assert sky_map_source_count(str(tmp_path / "missing.svg")) == 0


def test_svg_title_stripping_keeps_visual_geometry(tmp_path):
    source = tmp_path / "map.svg"
    source.write_text(
        '<svg><circle cx="1" cy="2" r="3" fill="red"><title>star 1</title></circle>'
        '<circle cx="4" cy="5" r="6" fill="blue"/></svg>',
        encoding="utf-8",
    )
    display = tmp_path / "display.svg"
    assert strip_svg_titles(str(source), str(display)) == str(display)
    text = display.read_text(encoding="utf-8")
    assert "<title>" not in text
    assert text.count("<circle") == 2
    assert 'r="3"' in text and 'r="6"' in text


def test_solution_parser_computes_fov_from_cd(tmp_path):
    solution = {
        "WCS": {
            "CRVAL1": math.radians(83.822),
            "CRVAL2": math.radians(-5.391),
            "CRPIX1": 0,
            "CRPIX2": 0,
            "CD": [
                [-4.0e-6, 0.0],
                [0.0, 4.0e-6],
            ],
        },
        "Method": "gaia",
        "RMSArcsec": 0.3,
        "NMatches": 12,
        "NStars": 30,
    }
    path = tmp_path / "light_plate_solution.json"
    path.write_text(json.dumps(solution))
    assert find_plate_solution(str(tmp_path)) == str(path)

    parsed = load_solution(str(path), 1000, 800)
    assert round(parsed.ra_deg, 3) == 83.822
    assert round(parsed.scale_arcsec_per_px, 2) == 0.83
    assert round(parsed.fov_width_deg, 3) == 0.229
    assert "Field of view" in parsed.summary()


def test_find_output_and_summarize_solution(tmp_path):
    nested = tmp_path / "results"
    nested.mkdir()
    per_image = nested / "IMG_4062_plate_solution.json"
    per_image.write_text(
        json.dumps({"ra_center": 83.82, "dec_center": -5.39, "fov_deg": 1.4, "status": "ok"})
    )
    assert find_output(str(tmp_path), [".json"]) == str(per_image)
    summary = summarize_solution(str(per_image))
    assert "fov_deg: 1.4" in summary


def test_auto_solve_uses_published_blind_catalog_when_available():
    adapter = SkyStackerAdapter()
    adapter.catalog_dir = "/tmp/catalogs"
    argv = adapter.build_plate_solve_argv("a.jpg", "/tmp/out", solver="auto")
    assert argv[:2] == ["/usr/bin/env", "SKYSTACKER_CATALOGS=/tmp/catalogs"]
    assert "--blind-catalog" in argv
    assert argv[argv.index("--blind-catalog") + 1] == "mag07"
