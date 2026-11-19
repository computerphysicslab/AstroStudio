"""Gaia DR3 local cache helpers."""

import os
from typing import List


def default_cache_dir() -> str:
    base = os.environ.get("XDG_CACHE_HOME") or os.path.expanduser("~/.cache")
    return os.path.join(base, "astro-studio", "gaia_cache")


def tile_count(cache_dir: str) -> int:
    if not cache_dir or not os.path.isdir(cache_dir):
        return 0
    return sum(
        1
        for _root, _dirs, files in os.walk(cache_dir)
        for name in files
        if name.endswith(".json")
    )


def gaia_flags(cache_dir: str, nside: int, offline: bool) -> List[str]:
    argv = ["--gaia-nside", str(nside)]
    if cache_dir:
        argv.extend(("--gaia-cache-dir", cache_dir))
    if offline:
        argv.append("--gaia-offline")
    return argv
