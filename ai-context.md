# Astro Studio — ai-context.md (unified operational summary)

> **Living file and operational source of truth.** Any AI working on this project must read it at
> the start of a session and update it **in the same change** whenever something important is
> learned (decisions, bugs, paths, state). For chronological history and normative specifications,
> see the sources in §11.
>
> - **Canonical path:** `/home/jips/datos/datos-juan/proyectos/astronomia/AstroStudio/ai-context.md`
> - **Created:** 2026-11-21
> - **Last updated:** 2026-11-21
> - **Language:** all context files in English; project code, comments and documentation in English.

---

## 1. Identity and current state

- **Application:** Astro Studio — a **zero-pixel-processing** GTK orchestration front-end for
  astronomical and photographic CLI backends.
- **Path:** `/home/jips/datos/datos-juan/proyectos/astronomia/AstroStudio`
- **Repo:** public `computerphysicslab/AstroStudio`, branch `main` (English commit messages;
  **never** push/tag/merge/rewrite history without an explicit request).
- **HEAD:** `3f63f9d` ("Fix CI Python environment and complete roadmap items 1-9").
- **Version:** `0.3.24` (`astrostudio/__init__.py:3`), committed on `main` and pushed to
  `origin/main`; working tree clean. `BUILD_DATE = "2026-11-21"`.
- **Stack:** Python 3.8-compatible runtime (mypy targets 3.9; CI uses system Python 3.10 on
  Ubuntu 22.04), PyGObject, **GTK 3.24 only** (GTK4 not installed), `Gio.Subprocess`,
  `GdkPixbuf`, Cairo.
- **Entry point:** `python3 -m astrostudio` → `app.main()`.

## 2. Critical rules (non-negotiable)

1. **Zero-processing GUI:** no stacking, calibration, demosaicing, stretching or pixel math in
   the application. Every action collects parameters, builds a sanitized `argv`, spawns an
   external CLI asynchronously and renders the file that backend wrote.
2. **Dual-format invariant:** every opened image has `working.tiff` (16-bit, the only CLI input)
   and `preview.png` (8-bit, the only file the GUI renders). A transform replaces the TIFF and
   regenerates the PNG; no pixel math in the GUI.
3. **`argv` arrays, never shell strings.** No blocking calls on the GTK main thread. The only
   deliberate exception is `adapters/remote.py`, which uses `shlex.quote` for the remote `ssh`
   command.
4. **Originals stay intact:** outputs go to `<XDG_RUNTIME_DIR>/astro-studio/<session>/<job>/`
   (fallback `/tmp/astro_studio_<pid>/`) or an explicit export path.
5. **Startup backend discovery:** `BackendRegistry.probe()` checks installation and versions
   asynchronously and drives menu sensitivity. Keep `ACTION_BACKENDS` and `IMPLEMENTED_ACTIONS`
   in sync. A missing backend leaves the action visible but disabled; **never** fabricate a
   result or fall back to in-process processing.
6. **No Parameter Inspector:** menus/dialogs ask for intent; the GUI generates adapter flags.
   Resize percentages live in Processing > Resize Image; double-click on the canvas is Fit to
   Window.
7. **Right dock:** its order and visibility must always be accurate here and in
   `Context/AstroStudio_ai_project_context.md` (§6). Transforms preserve zoom/pan.
8. **Logs:** the Terminal records timestamped CLI `argv` and responses, not installation status
   or metadata tags; it is closable/restorable from View. The persistent JSONL log records all
   operations for cost estimation.
9. **UI languages:** EN/ES/DE/JA/RU/ZH; keep `core/i18n.py` complete when adding menus, panels
   or status messages.
10. **Version control:** every implementation commit bumps `PATCH` at minimum and adds a
    `CHANGELOG.md` entry; `MINOR` marks roadmap milestones.

## 3. Architecture and code map

~14,600 Python lines in ~100 files (56 `test_*.py`).

- `astrostudio/__main__.py` → `app.py:84` `AstroStudioApplication(Gtk.Application)`
  (`application_id="org.astrostudio.gui.v2"`, `HANDLES_OPEN`, `do_open`/`do_command_line` for
  *Open With*). Registers `Gio.SimpleAction` for every `ACTION_NAMES` entry (`app.py:108`),
  default shortcuts (`app.py:48`) and dispatches `action_<name>` (`app.py:141`).
- `astrostudio/ui/` — GTK views:
  - `main_window.py` (~3,950 lines) — `MainWindow`, `MENU_LAYOUT` (10 menus: File, Edit,
    Processing, Astrometry, Arithmetic, Color, Filter, View, Options, Help), `IMAGE_EXTENSIONS`
    (18), `TOOL_ITEMS` (11), `TOGGLE_PANELS`.
  - `preview.py` — `PreviewPane` (Cairo, zoom/pan, selection, star/object overlays, preview
    pyramid, `size-allocate` level refresh).
  - `histogram_panel.py`, `resource_monitor.py`, `job_panel.py`, `dock_manager.py`,
    `menu_builder.py`, `action_registry.py`, `dialogs.py`, `window_utils.py`.
- `astrostudio/core/` — orchestration and pure helpers (52 type-checked modules):
  - `image_workspace.py:46` `ImageWorkspace` — `prepare()` (150), `_make_preview()` (272),
    `update_preview()` (314), `transform()` (324), `transform_via_image_op()` (354),
    `_finish_transform()` (448), `export()` (483), `undo()`/`redo()` (576/595),
    `ensure_pyramid()` (73).
  - `backends.py:255` `BackendRegistry` — 17 `BACKENDS` (40), `ACTION_BACKENDS` (61),
    `IMPLEMENTED_ACTIONS` (163), `probe()` (286), `is_action_enabled()` (339).
  - `process_engine.py:56` `ProcessEngine.run()` (74) — `Gio.Subprocess`, async pipes,
    configurable timeout (SIGTERM→SIGKILL), `cli_start`/`cli_end` metrics.
  - `command_builder.py:8` `CommandBuilder.build()` (27) — sanitized argv, NUL rejection.
  - `scratch.py:12`, `operation_log.py:10` (JSONL, 20 MB/3-backup rotation), `settings.py:37`,
    `i18n.py:1060` `Translator`.
  - Catalogs/reports: `sky_filters.py` (24 filters), `export_formats.py` (12 formats),
    `catalog_hints.py` (distinctive-word matching with typo tolerance), `astrometry.py`
  (`sky_map_source_count()`),
    `plate_solution.py`, `wcs.py`, `star_catalog.py`, `object_classification.py`,
    `quality_dashboard.py`, `frame_quality.py`, `pipeline_graph.py`, `pipeline_export.py`,
    `provenance.py`, `estimator.py`, `hot_folder.py`, `offline_prefetch.py`, `plugins.py`,
    `gaia_cache.py`, etc.
- `astrostudio/adapters/` — 9 connectors: `magick.py` (resolves `magick` or `convert`, explicit
  `png:` coder and `build_pyramid_argv()`), `skystacker.py` (image-ops, plate solve, sky-map,
  survey-cutout, stars, classify, BPM, CR2), `siril.py`, `astrometry.py` (`solve-field`/ASTAP),
  `exiftool.py`, `base.py`, `remote.py`, `fits_compression.py`, `external_pipelines.py`.
- `astrostudio/data/` — `openngc_hints.json` (875 kB, 13,643 objects), `CREDITS.md`, CC BY-SA 4.0
  license.
- `tests/` — 56 files, 211 passing tests: argv/flags, dual-format workspace, ENOENT/exit codes/
  timeouts/cancellation, log/scratch, parsers, GUI under `xvfb`, real CLI integration (skipped
  without ImageMagick), opt-in benchmark. No Hypothesis (only a stale `.hypothesis/` directory).
- `scripts/` — `analyze_operations.py` (p75 s/MP model → CSV + `estimates.json`),
  `export_pipeline.py`.

## 4. Image and export flow

1. `prepare()` creates the scratch `image-NNNN` directory; FITS/RAW/PSD get `display_stretch`,
   HDU validation (`fits_hdus.py`) and SkyStacker native decoding for CR2; otherwise
   `build_import_argv()` → `working.tiff`.
2. `_make_preview()` renders `preview.png.next` via CLI and promotes it with `os.replace()`.
3. `transform()` operates on the TIFF → `working_next.tiff`, snapshots via hardlinks
   (`history_depth=10`), checks a content-hash cache, then `_finish_transform()` replaces the
   TIFF and regenerates the PNG.
4. `update_preview()` regenerates only the PNG (histogram level/gamma); the high-depth TIFF is
   untouched.
5. Undo/Redo restores TIFF+PNG snapshots, isolated per image; zoom/pan are preserved.
6. `export()` copies the PNG for `png8`; every other format is written by the CLI from the TIFF
   (scientific exports stay linear). The format is chosen **before** the destination;
   `unique_export_path()` adds `-1`, `-2`… and falls back to a short UUID after 10,000
   collisions.
7. `ensure_pyramid()` generates real 25%/50% levels via CLI `-resize`; `PreviewPane` selects a
   level by zoom and validates its dimensions against `logical_size × level_scale`.

## 5. Right dock state (refresh on every iteration)

Top to bottom (`main_window.py:_build_layout()`, ~561-604):

| Panel | Default visibility | Toggle / notes |
|---|---|---|
| CPU/RAM Resources | visible | `action_toggle_resources`; 1 s `GLib.timeout_add`; `CPU <overall>% (core <peak>%)` |
| Backends | **hidden** (`show_backends=false`) | `action_toggle_backends` (persisted); installed-first alphabetically; X and restorable; menu gating |
| Metadata | **hidden** (`set_no_show_all(True)`) | (i) opens a floating ExifTool window with PNG/TIFF tabs; secondary docked panel exists |
| Histogram | visible since v0.2.10 | `action_toggle_histogram`; between CPU/RAM and Terminal; 256 colours; low/high and gamma via CLI |
| Jobs | **hidden** (`show_jobs=false`) | job list with state/duration and retry by original argv; `action_toggle_jobs` persisted |
| Terminal Drawer | visible | `action_toggle_terminal`; syntax-highlighted timestamped argv/responses; auto-scroll; X and restorable |

Notes: on small screens the dock is a `Gtk.ScrolledWindow` (`right_scroll`); fullscreen hides
menus, toolbar, docks and status bar; the thumbnail strip is a left panel, hidden by default
(`show_thumbnails`). A View toggle stays enabled after its panel is closed with X.

## 6. Astrometry, catalogs and scientific guardrails

- SkyStacker bridge: `--image-op plate-solve` (with `--plate-center RA,DEC`), `sky-map`,
  `survey-cutout`, `measure-quality`, star export and object classification. Artifacts stay in
  scratch; `plate_solution.json` is normalized and cached per image. Failures are reported (0
  matched pairs on uncalibrated wide fields is a reproducible backend limitation, never a false
  "OK").
- Alternative solvers: `AstrometryAdapter` for `solve-field`/ASTAP; native blind solve with
  `--plate-solver native --blind-catalog mag07`.
- `catalog_hints.py` extracts M/NGC/IC/Caldwell IDs and common object names from filenames and
  prefills RA/Dec from OpenNGC. Distinctive-name words are matched with a one-character typo
  tolerance; exact full-name matches and explicit catalog IDs take priority; ambiguity is
  reported, never guessed. Example: `Dumbell-86x30s-refr150-crop_2.png` → M27 at
  299.901583, 22.721028; `Little-Dumbbell.png` stays ambiguous. Gaia cache defaults to
  `nside=64` and respects offline mode.
- Never fabricate synthetic bias/dark/flat frames; detect calibration folders case-insensitively;
  `--bpm-auto` with a 0.1% sanity cap; linear guards before nonlinear stretching; shear ≤0.10
  and anisotropy ≤1.10 in affine refinement; keep linear scientific artifacts separate from
  display-stretched previews.

## 7. Local test datasets (never commit)

- `assets/Orion-135mm/` — 66–67 JPG 2400x1600, uncalibrated wide-field M42 session (gitignored).
- `/home/jips/datos/Astro/datasets/OrionNebula/` — 134 CR2 lights, 22 darks, 17 flats, 5 biases.
- `/home/jips/datos/Astro/datasets/04_emission_nebula_Flame/` — 45 FITS lights, 2 darks, 1 flat,
  1 bias (3056x2048).
- Test outputs always in `/tmp/astro_studio_*`, never inside the source datasets.

## 8. Verified backend environment (2026-11-21)

- Installed: `exiftool` 13.50, **ImageMagick 7.1.2-18 for both `magick` and `convert`** (IM7 ships
  `convert` as a compatibility symlink), `skystacker` (first-party goTiff reader consumes the
  16-bit `working.tiff` directly), FFmpeg, GIMP, `libraw-bin` (`dcraw_emu -v` exits 1 despite
  printing "Using 8 threads", so the LibRaw probe reports an error).
- Missing: `rawtherapee-cli`, `siril-cli`, ASTAP, `solve-field`, GraphicsMagick → adapters report
  "backend unavailable"; no in-process fallback.
- TIFF→PNG preview rendering remains an external ImageMagick job.

## 9. Commands and verification

```bash
python3 -m astrostudio                                          # run
python3 -m compileall -q astrostudio tests                      # compile check
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/ -q    # tests (unrelated Dash plugin breaks autoload)
PYTHONPATH=. python3 tests/benchmark_operations.py              # opt-in benchmark
PYTHONPATH=. python3 scripts/analyze_operations.py              # CSV + timing model
python3 -m mypy --config-file mypy.ini                          # strict core/adapters
xvfb-run -a python3 -m pytest tests/ -q -p pytest_cov --cov=astrostudio/core --cov=astrostudio/adapters --cov-fail-under=70
desktop-file-validate packaging/astro-studio.desktop
```

CI (`.github/workflows/ci.yml`, Ubuntu 22.04) and pre-commit run mypy, pytest-cov (70% gate) and
desktop-file validation. `mypy.ini` has documented pragmatic exceptions and
`ignore_missing_imports` for `gi`, `numpy`, `PIL`. Current local environment: Python 3.14.4,
pytest 9.0.2, GTK 3.24.52 with glycin loaders, ImageMagick 7.1.2-18. Dev tools installed from apt
via `~/install-astrostudio-dev-tools.sh`: mypy 1.19.1, pytest-cov 5.0.0, pre-commit 4.5.1.
Latest verification: **234 passed, 2 skipped**, real GUI launch without GError, mypy clean on 52
modules (target 3.9 because mypy 1.19 dropped 3.8), 89% coverage with the 70% gate. With
`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, add `-p pytest_cov` so the coverage plugin loads.

- Operations: `$XDG_DATA_HOME/astro-studio/operations.jsonl`; preferences:
  `$XDG_CONFIG_HOME/astro-studio/settings.json`; timing model:
  `~/.local/share/astro-studio/{operations.csv,estimates.json}`.
- Desktop install: `./packaging/install.sh` (user level, no sudo); verify with `gio mime <type>`.

## 10. Work state and known discrepancies

- **Committed:** `9442050` (0.3.15–0.3.19 work, 25 files). **Uncommitted 0.3.20:** `CHANGELOG.md`,
  `README.md`, `astrostudio/__init__.py`, `packaging/appimage/AppImageBuilder.yml`,
  `astrostudio/core/astrometry.py`, `astrostudio/core/__init__.py`, `astrostudio/ui/main_window.py`,
  `tests/test_astrometry.py`, `tests/test_integration_cli.py`, `tests/test_ui_interactions.py` and
  both context files. Earlier uncommitted history (already in `9442050`): `requirements-dev.txt`
  (0.3.15 added numpy/Pillow/
  PyYAML; 0.3.16 replaced fixed pins with bounded ranges) plus, for 0.3.16–0.3.18,
  `astrostudio/adapters/magick.py`, `astrostudio/core/image_workspace.py`,
  `astrostudio/core/catalog_hints.py`, `astrostudio/ui/preview.py`, `astrostudio/ui/main_window.py`,
  `mypy.ini`, `astrostudio/core/settings.py`, `astrostudio/ui/dock_manager.py`,
  `astrostudio/core/astrometry.py`, `astrostudio/core/__init__.py`, `tests/test_adapters.py`, `tests/test_image_workspace.py`,
  `tests/test_integration_cli.py`, `tests/test_ui_startup.py`, `tests/test_ui_interactions.py`,
  `tests/test_preview_pyramid.py`, `tests/test_catalog_hints.py` and the context files. Nothing
  staged; do not commit without an explicit request.
- Ubuntu 24.04 regressions fixed: IM7 wrote `preview.png.next` as TIFF (`Invalid PNG signature`
  in glycin) → explicit `png:` coder; PSD import adds `-alpha off` (§76). Pyramid levels were
  full-size but labelled 0.25/0.5 → explicit `-resize`, dimension validation and
  `size-allocate` refresh (§77). Dumbbell filename hint (§78).
- `MENU_LAYOUT` contains actions absent from `IMPLEMENTED_ACTIONS` (e.g. `clone-stamp`,
  `arithmetic`, `color`, `gradient`, `deconvolution`, `geometry`, `derotator`, `calibration`,
  `stacking`, `line-profile`) → they appear disabled; `language` is in `ACTION_BACKENDS` but not
  in `IMPLEMENTED_ACTIONS`.
- Ignored residual caches: `.hypothesis/`, `.mypy_cache/`, `.pytest_cache/`, multi-version
  `__pycache__`. `Context/`, `assets/`, `screenshots/`, `*.jsonl`, `*.csv` are gitignored.
- Roadmap: milestones v0.1.0–v0.3.19 complete; outstanding: GTK 4 migration (post-v1.0.0),
  native XISF and BigTIFF/Astro-TIFF WCS (v0.5.0), compression-artefact dashboard (v1.0.0).
  Deferred inside "completed" items: histogram phase 2 click-to-anchor/GHS, tiling/GtkGLArea,
  flip/mirror, JPEG 4:4:4, PackBits.

## 11. Sources (authoritative detail)

| File | Content |
|---|---|
| `AGENTS.md` | Critical agent rules (living memory, zero processing, argv, living contexts). |
| `Context/AstroStudio_ai_project_context.md` | Living chronological/technical context (78 sections, ~1,200 lines). |
| `Context/GUI-specifications.md` | Authoritative menu/toolbar → backend catalog. |
| `Context/AstroStudio_software_architecture_cli_ecosystem_specification.md` | Orchestration engine and backend list. |
| `README.md` | User documentation, installation and manual verification. |
| `roadmap.md` | Milestones v0.1.0–v1.0.0, execution queue and format audit. |
| `CHANGELOG.md` | Version history and `MAJOR.MINOR.PATCH` policy. |
| `/home/jips/ai-context.md` | Global user context (working rules, Ubuntu system, other projects). |

## 12. Update log

- **2026-11-21:** created after analysing the whole tree (`astrostudio/`, `tests/`, `scripts/`,
  `packaging/`, `.github/`, configs) and the existing specifications. Kept as the operational
  summary; chronological detail stays in `Context/AstroStudio_ai_project_context.md`. Recorded
  the uncommitted 0.3.15 state and the right dock.
- **2026-11-21:** exhaustive test and log review (`operations.jsonl` + journal). Found and fixed
  the ImageMagick 7 preview regression (v0.3.16); verified with a real GUI launch (§76).
- **2026-11-21:** installed dev tools via `~/install-astrostudio-dev-tools.sh` and replaced fixed
  `requirements-dev.txt` pins with bounded ranges valid for CI Python 3.10 and local 3.14.
- **2026-11-21:** fixed the Fit to Window bug (v0.3.17): full-size pyramid levels labelled
  0.25/0.5 made the canvas draw images 2–4× too large; nine regression tests, including Cairo
  pixel sampling and a real-allocation GTK flow; 207 passed/2 skipped (§77).
- **2026-11-21:** diagnosed and fixed the Dumbbell catalog hint (v0.3.18): the real filename is
  `Dumbell-...` and matching required the verbatim phrase `dumbbell nebula`. Distinctive-word
  matching with one-character typo tolerance, exact-match priority and an explicit-ID guard
  were added; M27 resolves to 299.901583,22.721028. Suite 211 passed/2 skipped (§78).
- **2026-11-21:** Backends and Jobs panels now start hidden with persisted View toggles; Gaia Sky
  Map output is opened as a new canvas image with display stretch and explicit source-count/
  failure reporting instead of a dark floating window. Suite 218 passed/2 skipped (§79).
- **2026-11-21:** fixed the flat grey sky map (v0.3.20): IM7 drops SVG circles that contain
  `<title>` tooltips, so a cleaned display copy is rendered instead; 221 passed/2 skipped (§80).
- **2026-11-21:** reviewed the last session log (`9a930bea`): fixed the spurious LibRaw probe,
  the missing catalog environment in prefetch jobs, prefetch error reporting and plate-solution
  inheritance for the generated sky-map image. The remaining HiPS HTTP 404 is an external CDS
  outage and is now reported with a hint. Suite 226 passed/2 skipped (§81).
- **2026-11-21:** fixed three app-side errors from session `e0b66680`: IM7 `-convolve` flag order,
  survey prefetch without a plate center and the missing `filter-stretch` handler; 229 passed/
  2 skipped (§82).
- **2026-11-21:** session `21f9df83` contained only external failures; added structured failure
  classification and `external_failure` log events so future iterations can separate app bugs
  from backend outages; 231 passed/2 skipped (§83).
- **2026-11-21:** localised external-failure dialogs with literal stderr in smaller text, fixed
  terminal bottom scroll, and gated the Stop action to active user jobs; 234 passed/2 skipped (§84).
