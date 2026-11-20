"""Guardrails for linear-space operations before non-linear stretching."""

from typing import Iterable, List, Tuple

LINEAR_OPERATIONS = {
    "background",
    "deconvolution",
    "starless",
    "gradient",
    "filter-stretch",
}
NONLINEAR_OPERATIONS = {"stretch", "asinh", "mtf", "curves"}


def check_linear_guard(operations: Iterable[str], allow_override: bool = False) -> Tuple[bool, str]:
    """Return (allowed, reason) for a new linear operation in a pipeline."""
    history = list(operations)
    if any(name in NONLINEAR_OPERATIONS for name in history):
        if allow_override:
            return True, "override accepted"
        return False, "linear operation after non-linear stretch"
    return True, "linear space intact"
