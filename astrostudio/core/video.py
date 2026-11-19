"""SER and AVI helpers for planetary capture sequences."""

import struct
from dataclasses import dataclass
from typing import List

LOSSLESS_AVI_CODECS = {"DIB ", "Y800", "RGB ", "I420", "YV12", "HFYU", "FFV1", "ULRG", "LAGS"}
REJECTED_AVI_CODECS = {"MJPG", "DIVX", "XVID", "H264", "AVC1", "WMV1", "WMV2"}


@dataclass
class SerHeader:
    width: int
    height: int
    pixel_depth: int
    frame_count: int
    bayer_pattern: str
    camera: str


def parse_ser_header(path: str) -> SerHeader:
    with open(path, "rb") as handle:
        data = handle.read(512)
    if len(data) < 80 or data[:8] != b"SIMPLE\x00\x00":
        raise ValueError("not a SER file")
    camera = data[8:48].split(b"\x00", 1)[0].decode("utf-8", "replace")
    width, height, depth = struct.unpack_from("<III", data, 48)
    bayer = struct.unpack_from("<I", data, 60)[0]
    frames = struct.unpack_from("<Q", data, 72)[0]
    pattern = {0: "MONO", 1: "RGGB", 2: "BGGR", 3: "GRBG", 4: "GBRG"}.get(bayer, "UNKNOWN")
    return SerHeader(width, height, depth, frames, pattern, camera)


def validate_avi_codec(fourcc: str):
    code = fourcc.upper().strip()
    if code in REJECTED_AVI_CODECS:
        return False, "lossy codec %s rejected before stretching" % code
    if code in LOSSLESS_AVI_CODECS:
        return True, "lossless codec %s" % code
    return False, "unknown codec %s; refusing" % code


def ffmpeg_extract_argv(source: str, output_pattern: str, fps: str = None) -> List[str]:
    argv = ["ffmpeg", "-i", source, "-vsync", "0"]
    if fps:
        argv.extend(("-r", str(fps)))
    argv.append(output_pattern)
    return argv
