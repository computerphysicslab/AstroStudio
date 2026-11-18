# Astro Studio — Agent Memory

## Critical rules

- **Zero-processing GUI:** never implement stacking, calibration, demosaicing, stretching, or pixel math in the application. Every action collects parameters, builds a sanitized `argv`, spawns an external CLI asynchronously, and renders the file the backend wrote.
- **Context file is living documentation:** after *every* change to code, structure, specs, or tooling, update `Context/AstroStudio_ai_project_context.md` in the same change. Keep its sections accurate (identity, architecture, backends, guardrails, constraints, datasets, implementation baseline). Update the other files in `Context/` when their topic changes.
- `Context/GUI-specifications.md` is the authoritative menu/toolbar-to-backend catalog. `Context/AstroStudio_software_architecture_cli_ecosystem_specification.md` defines the orchestration engine and backend list.
- Never modify original input files; outputs go to `<XDG_RUNTIME_DIR>/astro-studio/<session>/<job>/` (fallback `/tmp/astro_studio_<pid>/`) or an explicit export path.
- Never use shell strings for CLI calls; `argv` arrays only. No blocking calls on the GTK main thread.
- Startup backend discovery (`BackendRegistry.probe`) checks installation and version of every CLI asynchronously and drives menu sensitivity. Keep `ACTION_BACKENDS` and `IMPLEMENTED_ACTIONS` in sync when adding adapters or actions.
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

`exiftool` is installed. `magick`, `rawtherapee-cli`, `siril-cli`, etc. may be absent: adapters must report "backend unavailable" rather than crash or fall back to in-process processing.
