# Astro Studio Roadmap

This roadmap tracks delivery of the zero-processing GTK orchestrator described in
`Context/AstroStudio_ai_project_context.md`. Status tags match the action tags in
`Context/GUI-specifications.md`: **[P1]** implemented, **[P2]** adapter/UI pending,
**[P3]** planned.

Non-negotiable rules for every item: no pixel math in the GUI, `argv` arrays only,
asynchronous subprocesses, scratch-only intermediate files, original inputs read-only,
and tests for every adapter. The pending backlog is ordered by difficulty, easiest
first; the milestone tags are a reference for release planning only.

## Current execution queue (next 30 minutes)

Immediate, small-scope items with explicit acceptance criteria. Keep this list
difficulty-ordered and move completed items into the v0.2.1 changelog.

1. [x] Rebuild the GTK menu bar whenever a dock is hidden/shown so the View items read
       `Backends Viewer: On/Off` and `Terminal Drawer: On/Off`. Acceptance: GUI smoke
       confirms the label flips after both the X button and the View action.
2. [x] Open metadata in a floating window with literal ExifTool output for PNG and TIFF
       and a close (X) button in its header. Acceptance: GUI smoke confirms the window,
       both tabs and literal `FileType` text.
3. [x] Verified the persistent operation log after real cycles: `cli_start`/`cli_end`,
       durations, exit codes and no pixel data; entries survive restarts.
4. [x] `cli_end` records now include `input_bytes`/`output_bytes` from existing files.
5. [x] CPU/RAM bars update every second via `GLib.timeout_add`, and the timeout is
       removed on `destroy`.
6. [x] `cleanup_job()` shares `job_dir()` sanitization with a regression test.
7. [x] `unique_export_path()` falls back to a short UUID after 10000 collisions.
8. [x] `Gio.DataInputStream` objects are closed in `ProcessEngine._maybe_finish()`.
9. [x] Backend status icons and apt-cache detail/install dialog; all dialogs draggable;
       Stop button restored; 40px progress bar (v0.2.8).
10. [x] Initial translation dictionary applied to menus, toolbar and key status messages.
11. [x] Window geometry hardening: scrollable right dock, minimum size below screen and
       startup validation so maximize/resize work (v0.2.31).

## Completed — v0.1.0 baseline

- [x] Coherent specifications: GUI actions delegate to CLI tools through scratch files.
- [x] GTK 3.24 / PyGObject skeleton: menu bar, toolbar, status bar, preview canvas,
      metadata panel, terminal drawer and user-level desktop installation.
- [x] Sanitized `CommandBuilder`, async `ProcessEngine`, scratch manager and startup
      `BackendRegistry` with version detection and menu gating.
- [x] Dual-format workspace: 16-bit `working.tiff` + 8-bit `preview.png`; every
      transform runs on the TIFF via CLI, replaces it and regenerates the PNG.
- [x] Undo/Redo via TIFF+PNG snapshots; zoom, pan and scroll state preserved across
      transforms and history operations.
- [x] ExifTool metadata on demand (PNG/TIFF tabs), chronological CLI log with
      timestamps/`argv`/responses, closable Backends/Terminal panels with View toggles.
- [x] Save As format picker (FITS, TIFF 16-bit uncompressed/LZW/Zip, PNG, JPEG 90/95%,
      BMP), desktop MIME associations, Open With support and astronomical file filters.
- [x] SkyStacker bridge: WCS-capable plate solve, Gaia sky map and survey cutout with
      `plate_solution.json` caching and real failure reporting.
- [x] Backends sorted installed-first alphabetically; busy (watch) cursor during jobs;
      FITS RGB/HDU import with `-combine` and CLI display stretch for dark previews.
- [x] Persistent preferences: installed-connector on/off state, language, theme, offline
      mode and thread limit in `Options > Backend Settings`, saved under XDG config.
- [x] Save As uses the original name with the chosen extension, adding `-1`, `-2`...
      only on collision; status bar reports size in MB and elapsed seconds.
- [x] Filter menu reorganized into submenus with more than ten ImageMagick-backed
      operations (blur, denoise, convolution, morphology, star-size reduction); fixed
      multi-token flags and edge/emboss arguments.
- [x] Theme preference actually applied via `Gtk.Settings`; View toggle labels show
      On/Off state; toolbar Undo/Redo buttons added.
- [x] Transform/export status reports elapsed seconds and active PNG/TIFF sizes in MB;
      Help > About dialog added with version and build date.
- [x] CPU/RAM bars colour-coded at 75%, syntax-highlighted terminal drawer, opt-in
      20 MP benchmark and analyzer producing CSV + incremental proportionality model;
      the GUI shows estimated seconds and a green progress bar before operations.
- [x] Test baseline and Git history on `main` (English commit messages).

## Pending backlog — ordered by difficulty (easiest first)

### Low difficulty

1. [x] Settings extended with binary overrides, scratch/cache directories and shortcut
       customization (v0.2.13).
2. [x] Default shortcuts for open/export/metadata/histogram/undo/redo/quit/fit plus
       persisted customization applied via `app.apply_shortcuts()` (v0.2.13).
3. [x] Drag-and-drop of files and folders onto the preview canvas (v0.2.13).
4. [x] Dark/light themes and configurable accent colours applied through GTK CSS.
5. [x] Export pipeline as shell script or Makefile from serialized `argv` (GUI + CLI).
6. [x] Content-hash cache (input bytes + argv) reuses identical TIFF transforms.
7. [x] Batch conversion adapter (`mogrify`) and dialog with format/destination selection.
8. [x] Resize percentages moved into Processing > Resize Image as a CLI submenu with
       Custom Scale; view-only Precise Scale removed (v0.2.6). Select Area toolbar
       overlay added (v0.2.16); crop via right-click and rotate menu added (v0.2.34); flip/mirror remain pending.
9. [x] Benchmark and estimator updated: p75 seconds/MP, separate resize-up/down,
       stretch-enabled preview timing and a visible lingering progress bar (v0.2.6).
9. [x] Histogram phase 1: CLI-generated histogram text in a dock between CPU/RAM and
       Terminal, logarithmic Y axis, preview vs working-TIFF distributions and two
       clickable/draggable low/high cut-point handles that trigger a CLI `-level` preview
       regeneration; pixel line profile still pending (v0.2.3).
10. [x] Localization of interface strings (EN/ES/DE/JA/RU/ZH).
11. [x] Small CPU/RAM level indicators using `psutil` with a `/proc` fallback, refreshed
       by `GLib.timeout_add()` in the right dock.
12. [x] Initial extended export formats via ImageMagick: PNG 16-bit, TIFF 32-bit float,
       FITS 32-bit float and flattened PSD. Remaining: JPEG 4:4:4 control, TIFF PackBits,
       BigTIFF and FITS tile-compression adapters (v0.2.3).
13. [x] `settings.threads` propagated to ImageMagick `-limit thread`.
14. [x] Operation-log rotation by size and `input_bytes`/`output_bytes` in `cli_end`.
15. [x] Collapsible error dialog with backend `stderr` details.
16. [x] Mermaid diagram, adapter contract docstrings, adapter checklist and known
       limitations documented.
17. [x] Unit-test gaps closed; corrupt-settings and malformed-histogram bugs fixed.

### Medium difficulty

1. [x] Visual job manager panel with states, durations and retry by original argv.
2. [x] Frame table with SkyStacker quality diagnostics (SNR, HFR, eccentricity,
       background sigma) for open images.
3. [x] Case-insensitive calibration folder discovery (Bias/Dark/Flat/Light) with
       light-frame exclusion.
4. [x] Siril adapter with calibration/stacking script generation, gated on siril-cli
       availability (binary not installed in this environment).
5. [x] BPM automation via SkyStacker `--bpm-auto` with 0.1% sanity-cap validation.
 6. [x] WCS values from plate_solution.json exported as a `.wcs.json` sidecar next to
        FITS outputs (installed tools cannot edit FITS headers directly).
 6a. [x] After a successful plate solve, enrich the image metadata with RA/Dec, pixel scale and
        field of view when those tags are absent. Never modify original files or delete existing
        tags: merge into a `.metadata.json` sidecar in scratch (and next to exports), keep existing
        coherent values and report conflicts instead of overwriting.
 7. [x] Direct ASTAP/solve-field adapters with seeds, scale hints and blind-scan warnings.
7a. [x] Native wide-field blind solve with `--plate-solver native --blind-catalog mag07`
       and automatic catalog discovery (v0.2.15).
8. [x] Gaia cache management with configurable nside, cache path and offline mode.
9. [x] Session save/resume with image paths, stretch points and plate solutions.
10. [x] Thumbnail strip for open images and before/after difference map via ImageMagick.
11. [x] WCS overlay marking the plate-solution reference pixel on the canvas.
12. [x] Argv builders for RAW developers, Hugin, enfuse and GIMP with backend gating.
13. [x] Parameter suggestions from metadata (ISO, exposure) and frame diagnostics.
14. [x] Markup annotations stored as data and burned in via ImageMagick `-draw`.
15. [x] Linear-space guard with optional override for post-stretch operations.
16. [x] Derivation tree dialog showing original, CLI operations and preview.
17. [x] Histogram phase 2 partial: shadow loupe, gamma slider mapped to CLI `-evaluate Pow`,
       while click-to-anchor and staged GHS remain planned:
       - Dual view: full 0–1 histogram with ghosted "before" and live "after", plus a
         shadow loupe magnifying the 0–0.05 region where linear astro data lives.
       - Parametric controls for GHS/Asinh (symmetry point, stretch factor, highlight
         protection) instead of only 3-point levels; Bezier curves deferred to the
         non-linear stage where they are actually usable.
       - Click-to-anchor: hovering the canvas draws a crosshair on the histogram at the
         sampled tone; clicking sets the symmetry point and dragging adjusts strength.
       - Semantic handles (black-point foot, target pivot, highlight knee) with snap and
         clipping counters; false-colour clipping overlay on the canvas.
       - Decouple display STF from data stretch and disable the preview stretch after a
         real stretch to avoid double-stretching; stage stack to commit/reorder stretches.
18. [x] FITS compression adapters for fpack algorithms (RICE_1/GZIP_1/GZIP_2/
       HCOMPRESS_1/PLIO_1) and gzip whole-file `.gz`.
19. [x] RAW/DNG metadata inspection with lossy and Bayer/linear-DNG warnings.
20. [x] SER header parser and ffmpeg frame extraction for lucky imaging.
21. [x] AVI codec validation via ffprobe, rejecting lossy codecs such as MJPEG.
22. [x] PSD/PSB read-back via ImageMagick `[0]` flattened composite with display stretch
       and an integration test (v0.2.4).
23. [x] First `MainWindow` refactor: extract `MenuBuilder`, `ActionRegistry`,
       `DockManager` and reusable dialogs; keep behaviour identical (v0.3.0).
24. [x] `mypy` strict on the core plus `pytest-cov` threshold (70% in `core/` and
       `adapters/`) in a pre-commit/CI job with `desktop-file-validate` (v0.3.0).
25. [x] UI smoke tests with PyGObject fixtures and `xvfb` that start the window and verify menus, dock
       toggles and metadata/histogram panels (v0.3.0).
26. [x] SIGKILL escalation after a configurable per-job timeout to avoid zombie jobs
       (v0.3.9).
27. [x] FITS multi-HDU detection with explicit errors instead of silent `-combine`
       failure on unusual files (v0.3.9).
28. [x] Structured logging: standard Python logger mirrored into `OperationLog` instead
       of ad-hoc `_log()` strings (v0.3.9).

### High difficulty

1. [x] Undo via operation replay / hardlinks with history depth policy instead of full
       TIFF+PNG copies (v0.3.12).
2. [x] Scalable previews: resolution pyramids and level-aware `GtkDrawingArea`
       rendering for large FITS/stacks (v0.3.12). Tiling and a `GtkGLArea` renderer remain
       deferred.
3. [x] Non-destructive visual pipeline graph: reorder, disable and duplicate nodes,
       exported as a reproducible script (v0.3.12).
4. [x] Hot-folder watcher that triggers calibration + stacking when new lights appear
       (v0.3.13).
5. [x] Smart catalog/HiPS prefetch for fully offline plate solving (v0.3.13).
6. [x] Quality-validation dashboard after stacking/calibration using backend metrics
       (v0.3.13).
7. [x] Plugin system with dynamic adapter registration via entry points (v0.3.14).
8. [x] Remote compute adapters (SSH/API argv builders) for heavy stacking (v0.3.14).
9. [x] Reproducible offline packaging manifests (Flatpak/AppImage) with optional
       dependencies declared (v0.3.14). Bundles are not built in CI.
10. [ ] Gradual GTK 4 migration once the runtime is available (post-v1.0.0).
11. [x] Filename-driven catalog hints for plate solving (v0.3.6, completed 2026-11-20). Many captures are named `Orion-M42-Riofrio-2026-11-09.png`; a
       tokenizer should extract `M42`, `NGC 1976`, `IC 434`, `Cxx` and common names,
       resolve them against a bundled offline catalog, and feed a trusted J2000 seed to
       SkyStacker as `--plate-center RA,DEC` (with existing focal-length/pixel-size
       hints). Ambiguous or multiple matches must never be fabricated: report the
       candidates and let the user choose or skip. Start with OpenNGC (NGC/IC/Messier/
       Caldwell cross-IDs and J2000 positions, CC BY-SA 4.0) plus its addendum for M40/
       M45; ship the license and attribution in the app. SIMBAD/CDS-derived extras are
       ODbL 1.0 and need separate attribution; original Dreyer NGC data is public domain.
       Avoid paywalled datasets. Acceptance: unit tests for filename parsing and
       ambiguity, argv tests for the seeded solver, and an integration test proving a
       named field no longer needs a blind solve.
12. [ ] XISF native read/write through an external CLI/library with LZ4/LZ4HC/Zlib/Zstd
       block compression, byte shuffling and checksum blocks (v0.5.0; no installed CLI
       covers this yet, so research is required).
13. [ ] BigTIFF (>4 GB) and Astro-TIFF keyword/WCS preservation end-to-end (v0.5.0).
14. [ ] Scientific validation dashboard for compression artefacts (banding from lossy
       RAW/JPEG/MJPEG before stretch, clipping counters, FWHM/SNR) (v1.0.0).

## Format coverage audit (reference)

| Format | Status via CLI | Notes / next step |
|---|---|---|
| FITS `.fits/.fit/.fts` | supported | First HDU or `-combine` import; 16/32-bit export |
| FITS tile compression `.fz`, GZIP_2 | planned | Needs `fpack`/`funpack` adapter (medium) |
| TIFF / BigTIFF | supported / planned | ZIP/LZW exported; BigTIFF needs `-define tiff:bigtiff` |
| XISF `.xisf` | planned | No installed CLI; research external reader/writer (high) |
| RAW `.cr2` | supported | SkyStacker native decoder → 32-bit float TIFF workspace |
| RAW `.cr3/.nef/.arw/.raf/.orf/.rw2` | partially supported | Import via ImageMagick; RAW developers pending (medium) |
| DNG `.dng` | planned | RawTherapee/LibRaw adapter with linear vs Bayer warning |
| SER `.ser` | planned | Siril/ffmpeg for 8/16-bit uncompressed sequences |
| AVI `.avi` | planned | ffmpeg, uncompressed/lossless only |
| PSD/PSB | supported | `-flatten` composite, flattened export |
| PNG 8/16-bit | supported | 16-bit via `png:bit-depth=16` |
| JPEG | supported | Quality presets; 4:4:4 control pending |
| Astro-TIFF (FITS header in TIFF tag 270) | planned | Read/write FITS keywords in ImageDescription; preserve orientation and BAYERPAT (medium) |
| `.f32raw` / `.f64raw` float planes | planned | SkyStacker intermediate format for linear pipelines (medium) |
| OpenEXR / PFM / RGBE HDR | planned | darktable/LibRaw interchange for 32-bit float HDR (medium) |
| Bayer dumps `.bay` / `.raw` | planned | Mono sensor matrices without EXIF; need debayer backend (medium) |
| Extended camera RAW (3FR, ARI, BMQ, CAP, CRW, ERF, IIQ, MEF, MOS, MRW, NRW, PEF, RDC, RW1, SR2, SRF, SRW, STI, X3F, CINE) | planned | darktable/LibRaw via adapter, with governed camera whitelist (medium-high) |
| Planetary video MP4/MOV (H.264/HEVC) | planned | ffmpeg-based frame extraction/SER conversion; refuse fragmented/10-bit variants (high) |
| WebP / JPEG XL / JPEG 2000 (JP2, J2K) | planned | Display/sharing formats via external CLI (low-medium) |

## Next three items (completed 2026-11-20)

With all low-difficulty items complete, the next three are the medium-difficulty core
quality items, in this order:

1. **#23 `MainWindow` refactor** — `astrostudio/ui/main_window.py` is now the single point
   of failure for menus, popups, docks, exports and transforms. Extract `MenuBuilder`,
   `ActionRegistry`, `DockManager` and dialogs first so later fixes are local and testable
   without changing behaviour. This unblocks reliable coverage of #24 and #25.
2. **#24 `mypy` strict + `pytest-cov` gate + `desktop-file-validate`** — after the
   refactor the core/adapters have stable boundaries. Add config and CI checks with 70%
   coverage in `core/` and `adapters/`; this protects the argv-only/zero-processing
   invariants and catches regressions in new report parsers.
3. **#25 PyGObject UI smoke tests** — current UI tests are hand-written and already
   cover popups, docks and close/undo behaviour under `xvfb` in CI; they do not need
   an unavailable `pytest-gtk` package.
   Do this after #23 so tests target the extracted components instead of the God Object.

Acceptance remains as listed above; update this section whenever the order changes.

## Milestone mapping (reference only)

- **v0.2.0** — conversion/inspection completeness, settings persistence, job manager.
- **v0.3.0** — MainWindow refactor, strict typing/CI, UI smoke tests and layer toggles.
- **v0.3.1-v0.3.4** — SkyStacker filter menu, overlay rendering fixes and Cairo path fix.
- **v0.3.5** — native SkyStacker TIFF input and catalog-hint research.
- **v0.3.6** — filename-driven catalog hints (roadmap 11).
- **v0.3.7** — log review, time-model refresh and documentation audit.
- **v0.3.8** — public repository preparation and CI/type-check hardening.
- **v0.3.9** — job timeout/SIGKILL escalation, FITS HDU validation and structured logging.
- **v0.4.0** — astrometry alternatives, WCS export and session resume.
- **v0.5.0** — extended backends and scalable previews.
- **v1.0.0** — full menu coverage, packaging and release.

## Version-control practice

- `main` is the integration branch; commit each logical change with a concise message
  in English.
- Keep `Context/AstroStudio_ai_project_context.md` updated in the same change as any
  code, structure, spec or tooling modification, and update this roadmap when status
  changes.
- Never commit scratch files, backups, large datasets or secrets; `.gitignore` excludes
  generated caches.
- No push, tag, merge or history rewrite without explicit user request.


### Completion note

Items 23-25 were completed in v0.3.0: `MenuBuilder`, `ActionRegistry`, `DockManager`
and `DialogFactory` were extracted from `MainWindow`; `mypy.ini`,
`requirements-dev.txt`, `.pre-commit-config.yaml` and `.github/workflows/ci.yml` enforce
strict core/adapters typing, 70% coverage and `desktop-file-validate`; GUI smoke tests
cover the window, menus, dock toggles and metadata/histogram panels. The local
environment lacks `mypy` and `pytest-cov`, so those checks run in CI with
the pinned dev requirements.


### Item 11 completion note

Implemented `core/catalog_hints.py` with a compact bundled OpenNGC projection (13,643
entries) including Messier/NGC/IC/Caldwell aliases and common names, plus CC BY-SA 4.0
license and CREDITS. `MainWindow._filename_hint()` prefills the Plate Solving dialog's
RA/Dec from an unambiguous filename match and logs ambiguous candidates instead of
guessing. Tests cover token extraction, M42/NGC1976/name aliases, ambiguity and the
bundled license files.


### Items 26-28 completion note

`ProcessEngine` now applies `settings.job_timeout_s` (default 1800 s): SIGTERM first, then
SIGKILL after `kill_grace_s`, with `job_timeout`/`job_killed` events in the operation log.
`core/fits_hdus.py` inspects headers before import and rejects multi-image or BINTABLE
layouts with an explicit message instead of a silent `-combine` failure.
`core/structured_log.py` mirrors standard Python log records into the terminal and the
JSONL operation log; `MainWindow._log()` delegates to it.


### CI dependency fix

`pytest-gtk==0.7` is not published on PyPI, so `pip install -r requirements-dev.txt`
failed before any check ran. UI smoke tests use plain PyGObject fixtures under
`xvfb-run`; the unused dependency was removed and `pytest==6.0.1` pinned to match the
validated local environment.


### High-difficulty items 1-3 completion note

`ImageWorkspace` now snapshots with hardlinks, trims `settings.history_depth`, writes
previews via atomic replace and restores snapshots through hardlinked temporaries.
Preview pyramids generate 25%/50% CLI-rendered levels and `PreviewPane` selects a level by
display scale while keeping full-resolution image coordinates. The pipeline export dialog
edits a `PipelineGraph` (move, disable, duplicate, remove) and writes only enabled nodes
as a reproducible shell/Makefile. Tiling/GtkGLArea is explicitly deferred.


### High-difficulty items 4-6 completion note

A GLib-timed `HotFolderWatcher` detects new light frames and writes/runs a Siril
calibration+stack script. `offline_prefetch` builds blind-catalog download and HiPS
survey-cutout argv jobs to warm local caches. The quality dashboard runs
`--image-op measure-quality`, parses the JSON/CSV report and flags low SNR, high HFR,
elongated stars and low quality.


### High-difficulty items 7-9 completion note

`core/plugins.py` discovers `astrostudio.adapters` entry points and registers adapters at
startup. `RemoteAdapter` builds SSH or HTTP-API argv lists for remote jobs. Flatpak and
AppImage manifests under `packaging/` declare the runtime, optional backends and license
notes; actual bundle builds remain a release-time step.


### Medium-difficulty item 6a completion note

`core/metadata_enrichment.py` proposes RA/Dec, pixel scale and FOV from a successful plate
solution and merges them into a `.metadata.json` sidecar in the image's scratch directory.
Existing keys are always preserved; coherent values are kept and conflicting ones are reported,
never overwritten. On FITS export the merged metadata is copied next to the exported file.
Original captures are never modified.


## Audit-driven robustness items (2026-11-21)

Shared scope: findings confirmed by source review in `reviews/informe_auditoria_AstroStudio.md`
and by the other audits. Evidence-only claims from screenshot reviews were filtered out.

- [x] **R1 — FITS inline comments**: strip ` / comment` from FITS cards so real files from
  Siril/ASTAP/cameras are not rejected as `missing SIMPLE=T`; keep quoted values intact.
- [x] **R2 — Preview generations**: unique job IDs and temporary PNGs per preview generation;
  cancel/supersede pending previews and discard stale callbacks so overlapping stretch jobs
  cannot overwrite each other or crash on `os.replace`.
- [x] **R3 — Histogram debounce**: trailing debounce (restart timer on each move) for stretch
  changes, shared with gamma, replacing the 1 s throttle that could launch several CLI jobs.
- [x] **R4 — Undo and active document**: create undo snapshots only after a successful
  transform; apply stretch and Close to the active image instead of the last opened one.
- [x] **R5 — Scientific-data warnings**: flag float FITS (`BITPIX < 0`) and 8-bit sources on
  `WorkingImage`; log explicit warnings that IM may rescale/clamp float data and that an 8-bit
  source promotes to 16-bit without adding real depth. Never modify the data silently.
- [x] **R6 — Cancellation escalation**: user cancellation escalates from SIGTERM to SIGKILL after
  `kill_grace_s`, with an accurate `job_killed` log event.
- [x] **R7 — FITS metadata**: report `BZERO/BSCALE`, `BLANK` and `DATAMIN/DATAMAX` from headers
  without decoding pixels, so photometric scaling is visible to the user.
