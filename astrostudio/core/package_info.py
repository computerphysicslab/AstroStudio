"""Map CLI binaries to apt packages and parse apt-cache policy output."""

PACKAGE_MAP = {
    "exiftool": "libimage-exiftool-perl",
    "convert": "imagemagick",
    "magick": "imagemagick",
    "gm": "graphicsmagick",
    "gimp": "gimp",
    "siril-cli": "siril",
    "astap_cli": "astap",
    "solve-field": "astrometry.net",
    "skystacker": "skystacker",
}


def package_for_binary(binary: str) -> str:
    name = binary.rsplit("/", 1)[-1]
    return PACKAGE_MAP.get(name, name)


def install_command(binary: str) -> str:
    return "sudo apt install %s" % package_for_binary(binary)


def parse_policy(text: str):
    installed = None
    candidate = None
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("Installed:"):
            installed = stripped.split(":", 1)[1].strip() or None
        elif stripped.startswith("Candidate:"):
            candidate = stripped.split(":", 1)[1].strip() or None
    return installed, candidate
