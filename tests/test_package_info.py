"""apt package mapping and policy parsing tests."""

from astrostudio.core.package_info import (
    install_command,
    package_for_binary,
    parse_policy,
)


def test_package_mapping_and_install_command():
    assert package_for_binary("/usr/bin/convert") == "imagemagick"
    assert package_for_binary("exiftool") == "libimage-exiftool-perl"
    assert install_command("convert") == "sudo apt install imagemagick"


def test_parse_policy():
    text = """\
convert:
  Installed: 8:6.9.10.23+dfsg-2.1ubuntu11.4
  Candidate: 8:6.9.10.23+dfsg-2.1ubuntu11.4
  Version table:
"""
    assert parse_policy(text) == (
        "8:6.9.10.23+dfsg-2.1ubuntu11.4",
        "8:6.9.10.23+dfsg-2.1ubuntu11.4",
    )
    assert parse_policy("") == (None, None)
