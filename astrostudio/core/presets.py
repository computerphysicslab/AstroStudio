"""Parameter suggestions derived from metadata and frame diagnostics."""

import re
from typing import Any, Dict, List, Optional


def parse_metadata_text(text: str) -> Dict[str, str]:
    result = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        if key:
            result[key] = value.strip()
    return result


def suggest_presets(metadata: Dict[str, str], quality: Optional[Any] = None) -> List[str]:
    suggestions = []
    iso = metadata.get("ISO", "")
    exposure = metadata.get("ExposureTime", "")
    try:
        if iso and float(iso) >= 1600:
            suggestions.append("Denoise: medium (high ISO %s)" % iso)
    except ValueError:
        pass
    if exposure and "/" in exposure:
        try:
            numerator, denominator = exposure.split("/", 1)
            if float(denominator) <= 30:
                suggestions.append("Sharpen: light (short exposure %s)" % exposure)
        except ValueError:
            pass
    if quality is not None:
        if quality.snr < 20:
            suggestions.append("Stack more lights: low SNR %.1f" % quality.snr)
        if quality.hfr > 3.0:
            suggestions.append("Refocus: HFR %.2f px" % quality.hfr)
    if not suggestions:
        suggestions.append("No strong suggestion; start with default presets")
    return suggestions
