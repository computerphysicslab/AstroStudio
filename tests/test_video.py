"""SER and AVI helper tests."""

import struct

from astrostudio.core.video import (
    ffmpeg_extract_argv,
    parse_ser_header,
    validate_avi_codec,
)


def test_ser_header(tmp_path):
    data = bytearray(80)
    data[:8] = b"SIMPLE\x00\x00"
    data[8:16] = b"Camera1\x00"
    struct.pack_into("<III", data, 48, 640, 480, 16)
    struct.pack_into("<I", data, 60, 1)
    struct.pack_into("<Q", data, 72, 100)
    path = tmp_path / "test.ser"
    path.write_bytes(data)
    header = parse_ser_header(str(path))
    assert header.width == 640 and header.height == 480
    assert header.pixel_depth == 16 and header.frame_count == 100
    assert header.bayer_pattern == "RGGB"


def test_avi_codec_validation():
    assert validate_avi_codec("Y800")[0]
    assert not validate_avi_codec("MJPG")[0]
    assert not validate_avi_codec("XYZW")[0]


def test_ffmpeg_argv():
    assert ffmpeg_extract_argv("in.ser", "out/%05d.png") == [
        "ffmpeg", "-i", "in.ser", "-vsync", "0", "out/%05d.png"
    ]
