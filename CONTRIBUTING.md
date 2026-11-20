# Contributing

Thanks for helping improve Astro Studio.

## Ground rules

- Keep the zero-processing mandate: never implement stacking, calibration, demosaicing,
  stretching or pixel math in the GUI. Add an adapter and build a sanitized `argv` list.
- Never modify original input images. Write outputs to scratch or an explicit export path.
- Do not block the GTK main thread; use `Gio.Subprocess` and callbacks.
- Keep `README.md`, `roadmap.md` and `CHANGELOG.md` accurate. The local `Context/`
  directory is agent memory and is intentionally not published.

## Development

```bash
python3 -m compileall -q astrostudio tests
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/
python3 -m mypy --config-file mypy.ini
```

`mypy.ini` uses strict mode with a few documented pragmatic exceptions for the
PyGObject/CLI codebase; new code should still be fully annotated.

For timing data:

```bash
PYTHONPATH=. python3 tests/benchmark_operations.py
PYTHONPATH=. python3 scripts/analyze_operations.py
```

## Pull requests

- One logical change per PR, English commit messages, bump `PATCH` in `__init__.py`.
- Add tests for new adapters, argv builders and UI regressions.
- Do not commit private datasets, screenshots, API keys, operation logs or local context.
