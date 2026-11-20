"""Read-only FITS HDU inspection for import validation."""

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

BLOCK = 2880
CARD = 80


@dataclass
class FitsHdu:
    index: int
    extension: str
    bitpix: int
    naxis: int
    dimensions: Tuple[int, ...]
    data_bytes: int


def _value(card: str) -> Any:
    if "=" not in card:
        return None
    raw = card.split("=", 1)[1].strip()
    if raw in ("T", "F"):
        return raw == "T"
    if raw.startswith("'"):
        return raw.strip("'").strip()
    try:
        return int(raw)
    except ValueError:
        return raw


def _read_header(handle: Any, offset: int) -> Tuple[List[str], int, bool]:
    cards: List[str] = []
    while True:
        handle.seek(offset)
        block = handle.read(BLOCK)
        if len(block) < BLOCK:
            return cards, offset, False
        for index in range(BLOCK // CARD):
            cards.append(block[index * CARD:(index + 1) * CARD].decode("ascii", "replace"))
            if cards[-1][:8].strip() == "END":
                return cards, offset + BLOCK, True
        offset += BLOCK


def inspect_fits(path: str) -> dict:
    """Return HDU metadata without decoding any pixels."""
    result: Dict[str, Any] = {"hdus": [], "error": None, "unusual": False}
    if not os.path.isfile(path):
        result["error"] = "FITS file not found: %s" % path
        return result
    hdus: List[FitsHdu] = []
    offset = 0
    index = 0
    try:
        with open(path, "rb") as handle:
            size = os.path.getsize(path)
            while offset < size and index < 64:
                cards, next_header, complete = _read_header(handle, offset)
                if not complete:
                    raise ValueError("HDU %d has no END card" % index)
                values = {}
                for card in cards:
                    key = card[:8].strip()
                    if key and key not in values and "=" in card:
                        values[key] = _value(card)
                if index == 0 and values.get("SIMPLE") is not True:
                    raise ValueError("missing SIMPLE=T primary header")
                extension = str(values.get("XTENSION", "PRIMARY")).strip()
                bitpix = int(values.get("BITPIX", 0))
                naxis = int(values.get("NAXIS", 0))
                dimensions = tuple(
                    int(values.get("NAXIS%d" % axis, 0)) for axis in range(1, naxis + 1)
                )
                data_bytes = 0
                if bitpix and all(dimensions):
                    data_bytes = abs(bitpix) // 8
                    for dimension in dimensions:
                        data_bytes *= dimension
                    offset = next_header + ((data_bytes + BLOCK - 1) // BLOCK) * BLOCK
                else:
                    offset = next_header
                hdus.append(FitsHdu(index, extension, bitpix, naxis, dimensions, data_bytes))
                index += 1
    except (OSError, ValueError, TypeError) as exc:
        result["error"] = "cannot inspect FITS HDUs: %s" % exc
        return result
    result["hdus"] = [vars(hdu) for hdu in hdus]
    if not hdus:
        result["error"] = "FITS file contains no HDU"
        return result
    image_hdus = [hdu for hdu in hdus if hdu.extension in ("PRIMARY", "IMAGE")]
    tables = [hdu for hdu in hdus if hdu.extension == "BINTABLE"]
    rgb_primary = (
        image_hdus and image_hdus[0].index == 0
        and image_hdus[0].naxis == 3
        and image_hdus[0].dimensions[-1] in (3, 4)
    )
    if tables or len(image_hdus) > 1 or (hdus[0].naxis > 3 and not rgb_primary):
        result["unusual"] = True
        result["error"] = (
            "unsupported FITS layout: %d HDU(s), %d image HDU(s), %d BINTABLE(s); "
            "export a single image HDU before opening"
            % (len(hdus), len(image_hdus), len(tables))
        )
    return result
