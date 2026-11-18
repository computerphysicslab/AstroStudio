# Astro Studio — Agent Memory

## Critical rules

- **Zero-processing GUI:** never implement stacking, calibration, demosaicing, stretching, or pixel math in the application. Every action collects parameters, builds a sanitized `argv`, spawns an external CLI asynchronously, and renders the file the backend wrote.
- **Context file is living documentation:** after *every* change to code, structure, specs, or tooling, update `Context/AstroStudio_ai_project_context.md` in the same change. Keep its sections accurate (identity, architecture, backends, guardrails, constraints, datasets, implementation baseline). Update the other files in `Context/` when their topic changes.
- `Context/GUI-specifications.md` is the authoritative menu/toolbar-to-backend catalog. `Context/AstroStudio_software_architecture_cli_ecosystem_specification.md` defines the orchestration engine and backend list.
- Never modify original input files; outputs go to `<XDG_RUNTIME_DIR>/astro-studio/<session>/<job>/` (fallback `/tmp/astro_studio_<pid>/`) or an explicit export path.
- Dual-format invariant: every opened image has a 16-bit `working.tiff` (only input to external CLI transforms) and an 8-bit `preview.png` regenerated from it (only file the GUI renders). A transform replaces the TIFF, then regenerates the PNG; no pixel math in the GUI.
- Never use shell strings for CLI calls; `argv` arrays only. No blocking calls on the GTK main thread.
- Startup backend discovery (`BackendRegistry.probe`) checks installation and version of every CLI asynchronously and drives menu sensitivity. Keep `ACTION_BACKENDS` and `IMPLEMENTED_ACTIONS` in sync when adding adapters or actions.
- Desktop integration: the `.desktop` entry must declare image `MimeType`s and `%F`; the app uses `HANDLES_OPEN` to load files passed by the file manager. Export asks for the format (FITS/TIFF/PNG/JPG/BMP catalog in `core/export_formats.py`) before the destination.
- Version control is active (`main` branch, English commit messages). Commit logical changes when asked; never push, tag, merge or rewrite history without explicit user request.
- `roadmap.md` tracks milestones v0.1.0-v1.0.0; update it and `Context/AstroStudio_ai_project_context.md` in the same change whenever status changes.
- Code, comments, identifiers, and documentation in English.

## Stack and layout

- Python 3.8, PyGObject (GTK **3.24** only; GTK4 not installed), `Gio.Subprocess`, `GdkPixbuf`.
- `astrostudio/` package: GTK views, CLI adapters, command builder, process engine, scratch manager.
- `tests/` for `argv` serialization, ENOENT, exit codes, cleanup.
- Entry point: `python3 -m astrostudio`.

## Commands

- Run app: `python3 -m astrostudio`
- Tests: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/` (autoload breaks on an unrelated Dash plugin).
- Compile check: `python3 -m compileall -q astrostudio tests`

## Environment note

`exiftool` and ImageMagick 6 as `convert` are installed (`magick` v7 is absent; adapters resolve either binary). `rawtherapee-cli`, `siril-cli`, etc. may be absent: adapters must report "backend unavailable" rather than crash or fall back to in-process processing. The installed `skystacker` CLI cannot decode TIFF, so do not use it for the TIFF-to-PNG step.
