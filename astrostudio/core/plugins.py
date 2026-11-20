"""Discover optional adapters exposed through Python entry points."""

from typing import Any, Dict, List

GROUP = "astrostudio.adapters"


def discover_plugins(group: str = GROUP) -> List[Any]:
    """Return adapter objects published under the configured entry-point group."""
    try:
        from importlib.metadata import entry_points
    except ImportError:
        return []
    try:
        found = entry_points()
    except Exception:
        return []
    if hasattr(found, "select"):
        selected = found.select(group=group)
    else:
        selected = found.get(group, [])
    adapters = []
    for item in selected:
        try:
            adapter = item.load()()
        except Exception:
            continue
        if getattr(adapter, "build_argv", None) is not None:
            adapters.append(adapter)
    return adapters


def register_plugins(target: Dict[str, Any], group: str = GROUP) -> List[str]:
    names = []
    for adapter in discover_plugins(group):
        name = getattr(adapter, "name", adapter.__class__.__name__)
        target.setdefault(name, adapter)
        names.append(name)
    return names
