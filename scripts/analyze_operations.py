#!/usr/bin/env python3
"""Analyse the persistent operation log into CSV rows and a time model.

The model stores incremental sufficient statistics per operation stage so it can be
updated whenever more measurements are available.
"""

import argparse
import csv
import json
import os
from datetime import datetime
from typing import Dict, List

from astrostudio.core.estimator import default_model_path
from astrostudio.core.operation_log import OperationLog

CSV_FIELDS = (
    "timestamp",
    "session",
    "stage",
    "program",
    "argv",
    "width",
    "height",
    "megapixels",
    "duration_s",
    "output_bytes",
    "format",
    "exit_code",
)


def stage_from_argv(argv: List[str]) -> str:
    if not argv:
        return "unknown"
    program = os.path.basename(argv[0])
    joined = " ".join(argv)
    options = (
        ("-resize", "resize"),
        ("-unsharp", "unsharp"),
        ("-blur", "blur"),
        ("-gaussian-blur", "gaussian-blur"),
        ("-median", "median"),
        ("-despeckle", "despeckle"),
        ("-morphology", "morphology"),
        ("-edge", "edge"),
        ("-emboss", "emboss"),
        ("histogram:info:-", "histogram"),
        ("--plate-solve", "plate-solve"),
        ("--sky-map", "sky-map"),
        ("--survey-cutout", "survey-cutout"),
    )
    for token, stage in options:
        if token in joined:
            return stage
    if program == "exiftool":
        return "metadata"
    if program == "convert" or program == "magick":
        return "export"
    return program


def build_rows(entries: List[Dict]) -> List[Dict]:
    rows = []
    for entry in entries:
        event = entry.get("event")
        if event == "cli_end":
            argv = entry.get("argv") or []
            rows.append(
                {
                    "timestamp": entry.get("timestamp", ""),
                    "session": entry.get("session", ""),
                    "stage": stage_from_argv(argv),
                    "program": os.path.basename(argv[0]) if argv else "",
                    "argv": " ".join(argv),
                    "width": "",
                    "height": "",
                    "megapixels": "",
                    "duration_s": entry.get("duration_s", ""),
                    "output_bytes": "",
                    "format": "",
                    "exit_code": entry.get("exit_code", ""),
                }
            )
        elif event == "benchmark_case":
            width = entry.get("width", 0) or 0
            height = entry.get("height", 0) or 0
            rows.append(
                {
                    "timestamp": entry.get("timestamp", ""),
                    "session": entry.get("session", ""),
                    "stage": entry.get("stage", ""),
                    "program": "benchmark",
                    "argv": "",
                    "width": width,
                    "height": height,
                    "megapixels": round(width * height / 1_000_000.0, 4),
                    "duration_s": entry.get("duration_s", ""),
                    "output_bytes": entry.get("output_bytes", ""),
                    "format": entry.get("format", ""),
                    "exit_code": "",
                }
            )
    return rows


def write_csv(rows: List[Dict], path: str) -> None:
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def update_model(rows: List[Dict], path: str) -> Dict:
    try:
        with open(path, "r", encoding="utf-8") as handle:
            data = json.load(handle)
    except (OSError, ValueError):
        data = {}
    stats = data.get("stats", {})
    for row in rows:
        if row["megapixels"] in (None, "") or row["duration_s"] in (None, ""):
            continue
        stage = row["stage"]
        x = float(row["megapixels"])
        y = float(row["duration_s"])
        if x <= 0 or y <= 0:
            continue
        entry = stats.setdefault(
            stage, {"n": 0, "sum_x": 0.0, "sum_y": 0.0, "sum_xx": 0.0, "sum_xy": 0.0}
        )
        entry["n"] += 1
        entry["sum_x"] += x
        entry["sum_y"] += y
        entry["sum_xx"] += x * x
        entry["sum_xy"] += x * y

    models = {}
    for stage, values in stats.items():
        n = values["n"]
        if n == 0:
            continue
        denominator = n * values["sum_xx"] - values["sum_x"] ** 2
        if denominator > 1e-9:
            slope = (
                n * values["sum_xy"] - values["sum_x"] * values["sum_y"]
            ) / denominator
        else:
            slope = values["sum_y"] / values["sum_x"] if values["sum_x"] else 0.0
        intercept = (values["sum_y"] - slope * values["sum_x"]) / n
        slope = max(0.0, slope)
        intercept = max(0.0, intercept)
        models[stage] = {
            "samples": n,
            "slope": round(slope, 4),
            "intercept": round(intercept, 4),
        }

    result = {
        "generated": datetime.now().isoformat(timespec="seconds"),
        "formula": "seconds = slope * megapixels + intercept",
        "models": models,
        "stats": stats,
    }
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", default=OperationLog().path)
    parser.add_argument("--csv", default=None)
    parser.add_argument("--model", default=default_model_path())
    args = parser.parse_args()

    log = OperationLog(args.log)
    rows = build_rows(log.entries())
    csv_path = args.csv or os.path.splitext(args.log)[0] + ".csv"
    write_csv(rows, csv_path)
    model = update_model(rows, args.model)
    print("CSV: %s (%d rows)" % (csv_path, len(rows)))
    print("Model: %s (%d stages)" % (args.model, len(model["models"])))
    for stage, values in sorted(model["models"].items()):
        print(
            "  %-16s n=%-4d %.3f s/MP + %.3f s"
            % (stage, values["samples"], values["slope"], values["intercept"])
        )


if __name__ == "__main__":
    main()
