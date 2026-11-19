"""RAW/DNG inspection and lossless/lossy guardrails."""

from typing import Dict, List

LOSSY_MARKERS = ("lossy", "jpeg", "cRAW", "compressed")
LINEAR_MARKERS = ("linear", "demosaiced", "rgb")


def raw_warnings(metadata: Dict[str, str]) -> List[str]:
    warnings = []
    compression = " ".join(
        str(metadata.get(key, "")) for key in ("Compression", "DNGCompression", "PhotoME_Compression")
    )
    lowered = compression.lower()
    if any(marker.lower() in lowered for marker in LOSSY_MARKERS):
        warnings.append("Lossy RAW compression detected; avoid before stretching")
    subtype = str(metadata.get("DNGBayerPattern", metadata.get("CFAPattern", "")))
    if subtype:
        warnings.append("Bayer CFA: %s" % subtype)
    elif any(marker in lowered for marker in LINEAR_MARKERS):
        warnings.append("Linear DNG (already demosaiced); calibration differs from Bayer RAW")
    if not warnings:
        warnings.append("No lossy-compression marker found in metadata")
    return warnings
