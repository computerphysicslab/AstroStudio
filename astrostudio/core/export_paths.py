"""Destination naming helpers for Save As / Export."""

import os


def unique_export_path(directory: str, stem: str, extension: str) -> str:
    """Return a path that does not overwrite an existing file.

    The preferred name is ``stem.extension``. If it already exists, ``-1``,
    ``-2``, ... is inserted before the extension.
    """
    suffix = extension.lstrip(".")
    base = os.path.join(directory, stem)
    candidate = "%s.%s" % (base, suffix)
    if not os.path.exists(candidate):
        return candidate
    for index in range(1, 10000):
        candidate = "%s-%d.%s" % (base, index, suffix)
        if not os.path.exists(candidate):
            return candidate
    raise RuntimeError("could not find a free export name for %s" % stem)
