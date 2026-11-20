"""Parse SkyStacker quality reports and apply validation thresholds."""

import csv
import io
import json
from dataclasses import dataclass
from typing import List, Tuple

SNR_MIN = 20.0
HFR_MAX = 3.0
ECC_MAX = 0.6
QUALITY_MIN = 70.0


@dataclass
class QualityRow:
    file: str
    width: int
    height: int
    stars: int
    hfr: float
    eccentricity: float
    bg_sigma: float
    snr: float
    quality: float

    def issues(self) -> List[str]:
        problems = []
        if self.snr < SNR_MIN:
            problems.append("low SNR")
        if self.hfr > HFR_MAX:
            problems.append("high HFR")
        if self.eccentricity > ECC_MAX:
            problems.append("elongated stars")
        if self.quality < QUALITY_MIN:
            problems.append("low quality")
        return problems


def parse_quality_report(text: str) -> List[QualityRow]:
    try:
        data = json.loads(text)
    except (ValueError, TypeError):
        data = None
    if isinstance(data, dict) and data.get("images"):
        return [
            QualityRow(
                str(item.get("file", "")),
                int(item.get("width", 0)),
                int(item.get("height", 0)),
                int(item.get("stars", 0)),
                float(item.get("median_hfr_px", 0.0)),
                float(item.get("median_eccentricity", 0.0)),
                float(item.get("bg_sigma", 0.0)),
                float(item.get("snr", 0.0)),
                float(item.get("quality", 0.0)),
            )
            for item in data["images"]
        ]
    rows = []
    reader = csv.DictReader(io.StringIO(text))
    for item in reader:
        try:
            rows.append(
                QualityRow(
                    str(item.get("file", "")),
                    int(item.get("width", 0)),
                    int(item.get("height", 0)),
                    int(item.get("stars", 0)),
                    float(item.get("median_hfr_px", 0.0)),
                    float(item.get("median_eccentricity", 0.0)),
                    float(item.get("bg_sigma", 0.0)),
                    float(item.get("snr", 0.0)),
                    float(item.get("quality", 0.0)),
                )
            )
        except (TypeError, ValueError):
            continue
    return rows


def summarize(rows: List[QualityRow]) -> Tuple[bool, List[str]]:
    issues = []
    for row in rows:
        for issue in row.issues():
            issues.append("%s: %s" % (row.file or "image", issue))
    return not issues, issues
