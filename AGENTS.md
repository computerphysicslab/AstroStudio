# Astro Studio — Agent Memory

## Critical rules

- **Zero-processing GUI:** never implement stacking, calibration, demosaicing, stretching, or pixel math in the application. Every action collects parameters, builds a sanitized `argv`, spawns an external CLI asynchronously, and renders the file the backend wrote.
- **Context file is living documentation:** after *every* change to code, structure, specs, or tooling, update `Context/AstroStudio_ai_project_context.md` in the same change. Keep its sections accurate (identity, architecture, backends, guardrails, constraints, datasets, implementation baseline). Update the other files in `Context/` when their topic changes.
- `Context/GUI-specifications.md` is the authoritative menu/toolbar-to-backend catalog. `Context/AstroStudio_software_architecture_cli_ecosystem_specification.md` defines the orchestration engine and backend list.
- Never modify original input files; outputs go to `<XDG_RUNTIME_DIR>/astro-studio/<session>/<job>/` (fallback `/tmp/astro_studio_<pid>/`) or an explicit export path.
- Dual-format invariant: every opened image has a 16-bit `working.tiff` (only input to external CLI transforms) and an 8-bit `preview.png` regenerated from it (only file the GUI renders). A transform replaces the TIFF, then regenerates the PNG; no pixel math in the GUI.
- Never use shell strings for CLI calls; `argv` arrays only. No blocking calls on the GTK main thread.
- Startup backend discovery (`BackendRegistry.probe`) checks installation and version of every CLI asynchronously and drives menu sensitivity. Keep `ACTION_BACKENDS` and `IMPLEMENTED_ACTIONS` in sync when adding adapters or actions.
- Desktop integration: the `.desktop` entry must declare image `MimeType`s and `%F`; the app uses `HANDLES_OPEN` to load files passed by the file manager. When adding a format, also add its MIME type to `packaging/astro-studio.desktop` and, for non-standard extensions, to `packaging/astro-studio-mime.xml`, then reinstall. Verify with `gio mime <type>`. Export asks for the format (catalog in `core/export_formats.py`) before the destination.
- No Parameter Inspector: menus/option dialogs ask for intent and the GUI generates adapter flags internally. Resize percentages live in Processing > Resize Image and transform the TIFF; double-click on the canvas performs Fit to Window.
- Terminal log records timestamped CLI argv and responses, not backend install status or metadata tags; it auto-scrolls and is closable/restorable via View. Backends panel is also closable/restorable. Undo/Redo restores TIFF+PNG snapshots. No user-facing Cancel button.
- Supported UI languages: EN/ES/DE/JA/RU/ZH. Keep `core/i18n.py` complete when adding menu items, panels or status messages.
- The right-hand dock state (CPU/RAM, Backends, Metadata, Histogram, Terminal), including visibility and order, must be recorded in `Context/AstroStudio_ai_project_context.md` and refreshed on every iteration so the opencode right panel is never stale. Transformations must preserve the preview zoom/scroll state.
- Astrometry bridge uses SkyStacker CLI with WCS-capable image ops (`--image-op sky-map --plate-solve`, `survey-cutout`); cache/reuse `plate_solution.json`, keep artifacts in scratch and report failures, never fabricate results. Star-match failures on real fields are a backend limitation (reproducible outside the GUI); ASTAP/solve-field alternatives are planned.
- Show a busy cursor for the whole job lifecycle and keep dock-toggle actions enabled after panels are closed. FITS/RAW previews need first-HDU selection and a CLI display stretch; scientific exports stay linear.
- Backends panel sorts installed-first alphabetically; canvas supports drag-to-pan and preserves zoom/pan across transforms. Open dialog must include upper/lowercase astronomical extensions. GTK 3.24 has no `set_min_content_size()` on ScrolledWindow.
- Version control is active (`main` branch, English commit messages). Every implementation commit bumps `PATCH` at minimum (MAJOR.MINOR.PATCH) and adds a `CHANGELOG.md` entry; `MINOR` marks roadmap milestones. Never push, tag, merge or rewrite history without explicit user request.
- All CLI jobs and GUI operations append to the persistent JSONL operation log (`$XDG_DATA_HOME/astro-studio/operations.jsonl`) with timing and argv for later cost estimation. Benchmark: `PYTHONPATH=. python3 tests/benchmark_operations.py`; analyzer: `PYTHONPATH=. python3 scripts/analyze_operations.py`.
- `roadmap.md` tracks milestones v0.1.0-v1.0.0; update it and `Context/AstroStudio_ai_project_context.md` in the same change whenever status changes.
- Code, comments, identifiers, and documentation in English.

## Stack and layout

- Python 3.8-compatible runtime (type checking targets 3.9 because mypy 1.19 dropped 3.8), PyGObject (GTK **3.24** only; GTK4 not installed), `Gio.Subprocess`, `GdkPixbuf`.
- `astrostudio/` package: GTK views, CLI adapters, command builder, process engine, scratch manager.
- `tests/` for `argv` serialization, ENOENT, exit codes, cleanup.
- Entry point: `python3 -m astrostudio`.

## Commands

- Run app: `python3 -m astrostudio`
- Tests: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/` (autoload breaks on an unrelated Dash plugin).
- Compile check: `python3 -m compileall -q astrostudio tests`

## Environment note

`exiftool` and ImageMagick 6 as `convert` are installed (`magick` v7 is absent; adapters resolve either binary). `rawtherapee-cli`, `siril-cli`, etc. may be absent: adapters must report "backend unavailable" rather than crash or fall back to in-process processing. The installed `skystacker` CLI decodes TIFF through its first-party goTiff reader, so SkyStacker image-op jobs may consume the 16-bit working TIFF directly; ImageMagick remains the TIFF-to-PNG preview renderer.
