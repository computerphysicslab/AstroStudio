"""Sanitized argv serialization for external CLI backends."""

from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple

FlagSpec = Tuple[str, str, Optional[Callable[[Any], str]]]


class CommandBuilder:
    """Build an argv list from adapter flag specs and GUI parameters.

    The result is always a list of separate arguments; no shell is involved at
    any point, so paths with spaces or special characters remain literal.
    """

    def __init__(
        self,
        binary: str,
        flag_specs: Iterable[FlagSpec] = (),
        defaults: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not binary or "\x00" in binary:
            raise ValueError("binary must be a non-empty string without NUL bytes")
        self.binary = binary
        self.flag_specs = tuple(flag_specs)
        self.defaults = dict(defaults or {})

    def build(
        self,
        inputs: Sequence[str],
        output: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> List[str]:
        values = dict(self.defaults)
        if params:
            values.update(
                {key: value for key, value in params.items() if value is not None}
            )

        argv = [self.binary]
        for flag, key, formatter in self.flag_specs:
            value = values.get(key)
            if value is None or value is False or value == "":
                continue
            if value is True:
                argv.append(flag)
                continue
            text = formatter(value) if formatter else str(value)
            if "\x00" in text:
                raise ValueError("argument values must not contain NUL bytes")
            argv.extend((flag, text))

        for path in inputs:
            if not path:
                continue
            if "\x00" in path:
                raise ValueError("input paths must not contain NUL bytes")
            argv.append(path)

        if output:
            if "\x00" in output:
                raise ValueError("output path must not contain NUL bytes")
            argv.append(output)

        return argv
