# Changelog

Version scheme: `MAJOR.MINOR.PATCH`.

- `MAJOR`: incompatible architecture or GUI stack change.
- `MINOR`: user-visible feature milestone (roadmap milestone completion).
- `PATCH`: each logical implementation, fix or tooling change.

Every implementation commit must bump `PATCH` at minimum and add an entry here.

## 0.3.30 — 2026-11-21

- Canvas framing: added View > Zoom Modes with Fit to Window, Fill Window, Fit Width and Fit Height. The mode is stored in the view state and survives transforms/Undo-Redo; all five UI languages have the new labels.
- Right dock: the histogram/resources area and the Terminal are now separated by a draggable vertical paned divider whose position is persisted (`right_dock_split`).
- Toolbar: grouped file/zoom/edit actions with separators, 32 px icons, clearer disabled styling and a red Stop button at the end.
- Added four regression tests. Suite: 246 passed, 2 skipped; mypy clean on 53 modules.

## 0.3.29 — 2026-11-21

- Documented the histogram's yellow shadow loupe (levels 0–13/255, one vertical line per level) in README and `Context/GUI-specifications.md`. Added a circular `i` button to the histogram panel header whose GTK tooltip explains it in the configured UI language (EN/ES/DE/JA/RU/ZH) and updates when the language changes.
- Added two regression tests. Suite: 242 passed, 2 skipped; mypy clean on 53 modules.

## 0.3.28 — 2026-11-21

- Added roadmap item 6a and its implementation: after a successful plate solve, RA/Dec, pixel scale and FOV are proposed from the solution and merged into a `.metadata.json` sidecar in the image's scratch directory (and next to FITS exports). `core/metadata_enrichment.py` never deletes or overwrites existing keys: coherent values are kept and conflicts are reported. Original captures are never modified.
- Added four regression tests. Suite: 240 passed, 2 skipped; mypy clean on 53 modules.

## 0.3.27 — 2026-11-21

- Session `5f86382b` failed on `-rotate` and `-crop` with the same IM7 ordering problem already fixed for `-convolve`. Generalised `ImageMagickAdapter.build_argv()`: all image-operation flags now follow the input paths (only `-limit thread` stays before them), so rotate/crop/convolve/morphology/unsharp/resize work uniformly. Verified with real CLI round-trips.
- Updated argv expectations and added an integration test for rotate and crop. Suite: 236 passed, 2 skipped; mypy clean on 52 modules. GitHub CI was green before this change.

## 0.3.26 — 2026-11-21

- Completed the CI repair: added `python3-gi-cairo` (PyGObject Cairo foreign types) to the workflow apt dependencies, since the pixel-level Cairo tests need both bindings and headers. Skipped the SkyStacker CLI integration test when the binary is absent in CI instead of failing on ENOENT. Extended the workflow-guard test with the new dependency.
- Verified locally with a PATH without `skystacker`: 14 passed/1 skipped in the affected files; full suite 235 passed/2 skipped, mypy clean.

## 0.3.25 — 2026-11-21

- Fixed the GitHub CI failure: `tests/test_preview_pyramid.py` imports `cairo` for pixel-level rendering assertions, but the workflow only installed `libcairo2-dev` (C headers), not the Python bindings. Added `python3-cairo` to the apt dependencies in `.github/workflows/ci.yml`.
- Added a packaging test that guards the workflow's required dependencies and quality steps. Suite: 235 passed, 2 skipped; mypy clean on 52 modules.

## 0.3.24 — 2026-11-21

- External backend failures now show a clear, localised explanation (EN/ES/DE/JA/RU/ZH) with the connector's literal stderr below in smaller text, via `_show_external_failure()`. Failure titles/hints were added to `i18n.py` for all five non-English UI languages.
- The terminal drawer now always scrolls fully to the last line (bottom-aligned `scroll_to_iter` plus an idle adjustment update).
- The Stop toolbar action is disabled by default and during internal probes; it is enabled only while a user job is active, and its state is refreshed on every job start/end.
- Added four regression tests (localised messages, terminal scroll, stop-action gating). Suite: 234 passed, 2 skipped; mypy clean on 52 modules.

## 0.3.23 — 2026-11-21

- Added structured classification of backend failures (`classify_backend_failure()`): HiPS service outages, star-matching failures, missing catalog manifests and argv-order errors now produce categories and actionable hints. Plate solving, survey cutouts and prefetch record `external_failure` events with the category in the persistent operation log, so later iterations can distinguish app bugs from external outages without rereading raw stderr.
- The permanent rule to review the latest operation-log session at the start of every iteration was added to `AGENTS.md` and the global context.
- Session `21f9df83` had only external failures (CDS HiPS HTTP 404, M31 seeded solve with 0 matched pairs and no blind fallback); no app-side regression was found. Added two regression tests; suite 231 passed, 2 skipped, mypy clean on 52 modules.

## 0.3.22 — 2026-11-21

- Fixed the `-convolve` transform failures: ImageMagick 7 needs the input image before the operation, so `ImageMagickAdapter.build_argv()` now moves `-convolve` and its kernel after the inputs (verified with a real CLI round-trip).
- Fixed the survey prefetch job that failed with "image needs a plate solution": it now receives `--plate-solve --plate-center` from the current plate solution when available (reproduced: only the external CDS 404 remains).
- Implemented the missing Asinh Stretch handler (`filter-stretch`), which previously logged "Action pending CLI adapter" and did nothing; it delegates to the SkyStacker `stretch` image op.
- Survey cutout/prefetch still report the external CDS HiPS outage with the actionable hint. Added six regression tests; suite 229 passed, 2 skipped, mypy clean on 52 modules.

## 0.3.21 — 2026-11-21

- Fixed three app-side errors from the last session log: the LibRaw backend probe no longer runs `dcraw_emu -v` (unsupported, exit 1); backends with no version flag are now reported as available/unknown without spawning a job. Offline prefetch jobs now carry the same `SKYSTACKER_CATALOGS` environment wrapper as other SkyStacker jobs (verified: catalog download now exits 0) and report stderr details plus a failure count instead of a bare "failed".
- The generated Gaia sky-map image now inherits the parent plate solution, centre and solver options, so follow-up astrometry actions can reuse them. Survey-cutout failures caused by the CDS HiPS outage (HTTP 404) now include an actionable hint about changing `survey_hips` or retrying; the outage itself is external to AstroStudio.
- Added six regression tests. Suite: 226 passed, 2 skipped; mypy clean on 52 modules.

## 0.3.20 — 2026-11-21

- Fixed the Gaia sky map appearing as a flat grey rectangle in the canvas. SkyStacker writes a `<title>` child in every star `<circle>`; ImageMagick 7's SVG renderer silently drops such circles, leaving only the dark background and footer text (verified: bright pixels 2,290 → 11,801 after the fix). `strip_svg_titles()` writes a display-only SVG copy without those tooltips and the PNG is rendered from that copy; the original SVG and source count are preserved and logged.
- Added three regression tests: title stripping keeps circle geometry, a real ImageMagick render shows stars only without titles, and the GUI preview job uses the cleaned SVG.
- Suite: 221 passed, 2 skipped; mypy clean on 52 modules.

## 0.3.19 — 2026-11-21

- The Backends and Jobs dock panels now start hidden (`set_no_show_all(True)`, settings `show_backends`/`show_jobs` default to false). Their View toggles still work, now persist the preference, and the panels stay hidden after leaving fullscreen.
- Gaia Sky Map results no longer open in a floating dialog: the generated PNG is opened through the normal workspace flow as a new image in the canvas, with a display stretch so the dark SVG map is readable. Rendering uses an explicit `png:` coder at 144 dpi (2×) and reports the number of catalogued sources in the log/status.
- Empty or failed sky maps are now reported with the backend stderr and artifact path instead of silently showing a black image. Added `sky_map_source_count()` and explicit `display_stretch` support in `ImageWorkspace.prepare()`.
- Added tests for dock defaults, sky-map argv/source validation, success/failure callbacks and forced display stretch. Suite: 218 passed, 2 skipped; mypy clean on 52 modules.

## 0.3.18 — 2026-11-21

- Fixed filename catalog hints for common object names. The last opened capture was named `Dumbell-86x30s-refr150-crop_2.png`; two causes prevented a seed: the misspelling `Dumbell`, and `resolve_filename()` requiring the full catalog phrase `dumbbell nebula` verbatim in the filename, so even `Dumbbell.png` produced no hint. The bundled OpenNGC data did contain M27/NGC 6853 at 299.901583, 22.721028.
- Name matching now accepts all distinctive words of a catalog name as whole words (ignoring generic words such as "nebula") with a one-character typo tolerance, prefers exact full-name matches over fuzzy ones, and skips fuzzy names when an explicit catalog ID is present. `Little Dumbbell` stays ambiguous instead of being forced to M27.
- Added four unit tests and a GUI test for the real misspelled filename. Suite: 211 passed, 2 skipped; mypy clean on 52 modules.

## 0.3.17 — 2026-11-21

- Fixed the fit-to-window regression: `ImageWorkspace._run_pyramid_job()` generated `preview_25.png`/`preview_50.png` with the normal preview argv (no `-resize`) while labelling them 0.25/0.5, so `PreviewPane._on_draw()` divided by `level_scale` and drew the image 2–4× too large. Added `ImageMagickAdapter.build_pyramid_argv()` with an explicit `-resize` percentage; adapters that cannot downscale now report no pyramid instead of mislabelled full-size levels.
- `PreviewPane` rejects any level whose pixbuf dimensions do not match `logical_size × level_scale`, and refreshes the selected level on `size-allocate` (resize, panel toggles, fullscreen). Double-click Fit to Window now takes precedence over rotation/selection modes.
- Nine regression tests: real-CLI level dimensions, workspace-generated level sizes, unsupported-adapter fallback, mislabelled-level rejection, Cairo pixel-level fit footprint, real-allocation open flow, and double-click fit in rotation mode.
- Verification: 207 passed, 2 skipped; mypy clean on 52 modules.

## 0.3.16 — 2026-11-21

- Fixed the Ubuntu 24.04 regression that broke every preview: ImageMagick 7 infers the output coder from the last extension, so `preview.png.next` was written as TIFF and GdkPixbuf/glycin rejected it with "Invalid PNG signature". `build_preview_argv()` now forces the `png:` coder explicitly and `_on_preview()` no longer derives the temporary path from `argv[-1]`.
- PSD/PSB imports now drop alpha after flattening, so the 16-bit working TIFF stays RGB with ImageMagick 7 (the previous IM6-only behaviour).
- Added a real-CLI regression test that checks the PNG signature of a `.png.next` output, a `format == "PNG"` assertion in the rotation test, and isolated the undo/redo UI test from stale `/tmp` files. UI tests now pin GTK 3 before importing `gi.repository.Gtk`.
- Refreshed `requirements-dev.txt`: fixed pins became compatible ranges (pytest <10, mypy <2, pytest-cov <6, pre-commit <5, numpy <3, Pillow <13, PyYAML <7) so the same file installs on both the CI Python 3.10 and the current Python 3.14 environment.
- `mypy.ini` now targets Python 3.9 because mypy 1.19 dropped 3.8; strict checks still pass on all 52 core/adapter modules.
- Verification: 198 passed, 2 skipped (Python 3.14.4, pytest 9.0.2, GTK 3.24.52, ImageMagick 7.1.2-18); a real GUI launch opening M31.jpg no longer raises a GError.

## 0.3.15 — 2026-11-20

- Added `numpy`, `Pillow` and `PyYAML` to CI dev requirements; the previous run failed collecting `test_integration_cli.py` and `test_packaging.py` because those imports were missing.
- Local verification: 197 tests pass with 90% coverage and mypy clean on 52 modules.

## 0.3.14 — 2026-11-20

- Roadmap high-difficulty items 7-9 implemented at adapter/manifest scope.
- Plugins are discovered from `astrostudio.adapters` entry points and registered at startup.
- Added `RemoteAdapter` with SSH and JSON API argv builders for remote compute jobs.
- Added Flatpak/AppImage manifests and an optional dependency declaration; bundles are not built in CI.
- Added unit tests; suite 197 passed, 2 skipped, mypy clean on 52 modules.

## 0.3.13 — 2026-11-20

- Roadmap high-difficulty items 4-6 implemented.
- Added a hot-folder watcher that detects new light frames and runs a Siril calibration + stacking script.
- Added offline catalog/HiPS prefetch jobs that warm SkyStacker blind-catalog and survey caches.
- Added a quality dashboard that parses SkyStacker measure-quality reports and flags low SNR, high HFR, elongated stars and low quality.
- Added unit tests; suite 191 passed, 2 skipped, mypy clean on 50 modules.

## 0.3.12 — 2026-11-20

- Roadmap high-difficulty items 1-3 implemented at MVP scope.
- Undo/redo snapshots use hardlinks with `history_depth` trimming; previews are written atomically so snapshots keep their original bytes.
- Added CLI-generated 25%/50% preview pyramids with zoom-aware level selection and preserved full-resolution coordinates.
- Export Pipeline now opens an editable node graph (reorder, disable, duplicate, remove) and exports only enabled jobs as shell/Makefile.
- Added unit tests; suite 184 passed, 2 skipped, mypy clean on 47 modules.

## 0.3.11 — 2026-11-20

- CI now uses the system Python 3.10 from Ubuntu 22.04 instead of `setup-python`, so the apt-installed PyGObject `gi` module is importable.
- Pinned `pytest==7.4.4` for Python 3.10 compatibility; mypy still targets Python 3.8 via `mypy.ini`.
- Local verification: 180 tests pass with 90% coverage and mypy clean on 45 modules.

## 0.3.10 — 2026-11-20

- Fixed CI dependency installation: removed unpublished `pytest-gtk==0.7`, pinned `pytest==6.0.1` and `pre-commit==3.5.0`, and clarified that UI smoke tests use PyGObject fixtures under `xvfb`.
- Documentation and roadmap wording updated to match the real CI setup.

## 0.3.9 — 2026-11-20

- Roadmap items 26-28 completed.
- Configurable per-job timeout with SIGTERM then SIGKILL escalation; timeout/kill events are recorded in the operation log.
- FITS HDU inspection before import now rejects multi-image and BINTABLE layouts with an explicit error instead of a silent `-combine` mistake.
- Structured Python logging mirrors records with levels and fields into the terminal and the JSONL operation log.
- Added unit and integration tests; 180 passed, 2 skipped, 90% coverage, mypy clean on 45 modules.

## 0.3.8 — 2026-11-20

- Repository preparation for a public GitHub release: MIT `LICENSE`, `CONTRIBUTING.md`, `SECURITY.md`, and `.gitignore` rules for local `Context/`, personal data, credentials, keys and runtime logs.
- `Context/` is no longer tracked; it remains as local agent memory. Tests no longer depend on ignored personal `assets/`.
- CI fixed: coverage runs with pytest-cov under `xvfb-run`; mypy strict baseline now passes with documented pragmatic exceptions for the PyGObject codebase.
- Code annotations completed in core/adapters; 171 tests pass with 90% coverage.

## 0.3.7 — 2026-11-20

- Reviewed the persistent log: 4,126 entries, 1,370 CLI completions and 16 failures, all attributable to known backend plate-solve limitations, two cancelled jobs, the fixed rotate-TIFF bug or a mistyped test path.
- Improved `scripts/analyze_operations.py` stage classification (`import`, `preview`, `transform`, `histogram`, `image-op-*`, `export-stars`, `classify-objects`) and megapixel derivation from readable CLI inputs.
- Regenerated the time model: 22 stages over 1,684 CSV rows; `import` 0.164, `preview` 0.392, `histogram` 0.223 s/MP + 6.7 s, `export-stars` 0.144, `classify-objects` 0.506 s/MP.
- Refreshed README, GUI specification, architecture/context baseline, milestone mapping and benchmark limits; suite remains 171 passed, 2 skipped.

## 0.3.6 — 2026-11-20

- Completed roadmap item 11: filename-driven catalog hints for plate solving.
- Bundled a compact offline OpenNGC projection (13,643 objects) with Messier/NGC/IC/Caldwell aliases, J2000 coordinates and common names, plus CC BY-SA 4.0 license and attribution files.
- The Plate Solving dialog now prefills RA/Dec from an unambiguous filename match (`Orion-M42-...`, `NGC1976-...`, `Orion Nebula`); ambiguous matches are logged and never used.
- Added unit and UI tests for parsing, aliases, ambiguity, argv hints and bundled license files; suite is 171 passed, 2 skipped.

## 0.3.5 — 2026-11-20

- SkyStacker now decodes TIFF via its first-party goTiff module; `transform_via_image_op()` passes the 16-bit working TIFF directly instead of rendering an intermediate PNG.
- Removed the obsolete "SkyStacker cannot decode TIFF" notes from AGENTS.md and project context.
- Added roadmap item 11 (high difficulty): filename-driven catalog hints for plate solving, with OpenNGC CC BY-SA 4.0 as the proposed bundled offline catalog and license/attribution requirements documented.

## 0.3.4 — 2026-11-20

- Fixed the real source of the connecting lines: Cairo's current point left by `show_text()` was connected to the next star arc. `cr.new_path()` now clears the path after each label and before each circle.
- Verified with a fresh process on `Rosetta.jpg`: the star overlay shows only circles and rank numbers, no graph lines.
- Added a regression test that renders two distant stars and checks the empty area between them stays clean.

## 0.3.3 — 2026-11-20

- Removed the confusing label leader lines from the live overlay and SVG sidecar.
- Every displayed star now shows its rank number immediately beside its circle.
- Hovering or highlighting a star circle also brightens and enlarges its rank label; hovering the label selects the same star.

## 0.3.2 — 2026-11-20

- Star-identification circles now scale logarithmically with flux; brighter stars get visibly larger rings in both the live overlay and the SVG sidecar.
- Rank labels have explicit leader lines; hovering them explains that SkyStacker's catalog contains no invariant-pattern field, only star photometry/morphology.
- Hovering a star circle, its leader or a diffuse object now highlights that item with a brighter, thicker outline; leaving the canvas clears the highlight.
- Added regression tests for flux-radius ordering, leader hit-testing and highlight rendering; suite is 163 passed, 2 skipped.

## 0.3.1 — 2026-11-20

- Filter menu expanded with 24 SkyStacker single-image presets: blur, unsharp/wavelet sharpen, polynomial/masked/multiscale/asymmetric/RBF background, STF variants, guided/wavelet/adaptive denoise, Richardson-Lucy/Wiener/grid deconvolution and three starless modes.
- Added a CLI-only intermediate pipeline (TIFF -> PNG -> SkyStacker image-op -> JPEG -> 16-bit TIFF -> preview) because SkyStacker cannot decode TIFF.
- Linear guard still applies to background, deconvolution and starless filters; backend gating marks new actions SkyStacker-only.
- Added argv, registration and real-CLI integration tests; suite is 160 passed, 2 skipped.

## 0.3.0 — 2026-11-20

- Roadmap milestone: first `MainWindow` refactor extracted `MenuBuilder`, `ActionRegistry`, `DockManager` and `DialogFactory` while preserving behaviour.
- Added `mypy` strict config for `core/`/`adapters/`, 70% coverage gate, pre-commit hooks and GitHub Actions CI with `desktop-file-validate`.
- Added GUI smoke tests and regression tests for layer toggles and no-segment rotation feedback.
- View > Layers toggles star-identification and diffuse-object overlays independently.
- A quick click without a segment now keeps rotation mode armed and reports "No segment drawn; rotation not applied".
- Suite: 157 passed, 2 skipped.

## 0.2.40 — 2026-11-20

- Fixed rotate-by-segment completion: restoring the default cursor used the nonexistent `Gdk.CursorType.DEFAULT`, raising before `_rotate_image()` on a realized window; now uses `LEFT_PTR` and logs/shows the applied angle.
- Restored `Open Recent` in the right-click File submenu; the manual popup now injects the same recent-image entries as the menu bar.
- Added regression tests for Open Recent, recent fallback, cursor restoration, completed segment dispatch and a real-CLI end-to-end workspace rotation that verifies the regenerated preview changes.
- Verified with a real X11 drag: segment -11.31° produced a successful ImageMagick rotation and preview refresh. Suite is 152 passed, 2 skipped.

## 0.2.39 — 2026-11-20

- Rotate-by-segment activation now ignores a short window of stray events from the closing popup, checks rotation mode before double-click zoom, and shows a translated "Draw a segment" hint next to the pointer with a crosshair cursor.
- Star and diffuse-object overlays now have hover tooltips with star rank/flux/HFR or object type/CAS/Gini/M20 data.
- Recent transforms are deduplicated by full parameter set; segment and free-angle rotations relaunch their interaction instead of reapplying the old angle.
- Added hover, translation, dedup and relaunch tests; suite is 147 passed, 2 skipped.

## 0.2.38 — 2026-11-20

- Fixed rotate-by-segment being cancelled by a stray button-release delivered when the popup closes; a release without an active segment no longer disables rotation mode.
- Fixed the star/object overlay renderer: pycairo uses `show_text`, not `fill_text`; the old call aborted drawing after the first circle. All up to 500 detections are now drawn, with labels on the 30 brightest.
- Star catalog terminal log now reports detection count, preview dimensions and top flux; overlays are cleared when a different image is loaded.
- Added regression tests for stray releases and complete star-layer rendering; suite is 144 passed, 2 skipped.

## 0.2.37 — 2026-11-20

- Added SkyStacker `--export-stars` and `--classify-objects` report-only jobs, with JSON parsers, numbered canvas overlays and SVG sidecars.
- Right-click popups are built explicitly with nested submenus and recent transforms; actions dismiss popups and dispatch directly to window handlers.
- Added `Ctrl+Y` redo accelerator with settings migration; closing an image restores the previous one.
- Low-depth export formats (JPEG/PNG/BMP) receive CLI gamma/level flags while FITS/TIFF stay linear.
- Added unit, real-CLI and UI interaction tests; suite is 142 passed, 2 skipped.

## 0.2.36 — 2026-11-19

- Rotation argv now includes `+repage`, fixing ImageMagick 6 "negative image positions unsupported" when writing rotated TIFFs.
- Rotate-by-segment is idempotent and dismisses open popups before activating, fixing the first-attempt failure.
- Before / After result is loaded as a new image in the canvas instead of a separate window.
- Unit and real-CLI integration tests for rotation and before/after loading.

## 0.2.35 — 2026-11-19

- Rotation-by-segment mode is mutually exclusive with area selection and resets after use, fixing the alternating rectangle bug.
- Undo/Redo toolbar buttons become insensitive and greyed when history is empty or exhausted.
- Resource meters expand dynamically: CPU takes all remaining dock width, RAM stays circle-sized.
- Fullscreen canvas now uses the complete 1366x768 screen.
- Added unit and UI tests for rotation lifecycle, toolbar sensitivity and meter layout.

## 0.2.34 — 2026-11-19

- Fullscreen now gives the canvas 1366x744 of a 1366x768 screen by hiding the preview frame label and right dock container.
- Right-click popups use the current pointer position and stay referenced until replaced; Crop Selection clears the selection after applying the CLI crop.
- CPU/RAM meters are asymmetric: CPU 200px with bar/per-core, RAM 84px circle only; titles and percentages are inside the circles.
- View > Panels submenu toggles Backends, Histogram, Terminal, Resources and Jobs.
- Processing > Rotate Image adds 90 CW, 90 CCW, free angle and rotation by drawn segment.
- Tests for panel submenu, rotation angle and context menu.

## 0.2.33 — 2026-11-19

- CPU/RAM dock panel is closable like the others; RAM circle placed to the right of CPU gauges.
- Fullscreen hides all chrome; a transient status/progress bar appears during jobs and hides 1s later.
- Right-click popup keeps widget references (fixes intermittent failures), shares the full application menu including Open Recent, and adds Crop Selection enabled only over a selection.
- Derivation Tree fixed (`set_min_content_size` was invalid in GTK 3.24).
- Unit/integration tests for selection geometry, context menu and derivation dialog.

## 0.2.32 — 2026-11-19

- Gamma slider is debounced (one CLI preview job per 800ms) and logs the applied value.
- Thumbnails respond to single click, clear when images are closed, and are hidden by default; Frontend Settings toggles them.
- Replaced Maximize toolbar action with FullScreen (ESC exits). Right-click canvas shows a floating `menu` entry that opens the full application menu.
- Open Recent moved directly below Open in the File menu.
- Frontend Settings can hide CPU/RAM indicators; RAM linear bar removed, circle only.

## 0.2.31 — 2026-11-19

- Root cause of non-maximizable window fixed: right dock was forcing a 868px minimum, taller than the 768px screen. Dock is now scrollable with reduced panel minimums (window minimum 258px).
- Added startup geometry validation that logs min/screen sizes and hides optional panels if a future change reintroduces an oversized minimum.
- Added unit and opt-in X11 integration tests for window geometry and maximization.

## 0.2.30 — 2026-11-19

- Fixed 16-bit histogram collapse: CLI now emits 8-bit histogram data and the parser
  scales 16-bit components, so the working TIFF shows a real distribution.
- Screenshots directory ignored by Git.

## 0.2.29 — 2026-11-19

- Status bar now shows the running version at startup (`Astro Studio vX.Y.Z ready`).
- Plate-solve failures show actionable backend hints (install astrometry.net/ASTAP, set AN_API_KEY, use a linear frame with a precise seed) in the expandable error dialog.

## 0.2.28 — 2026-11-19

- CPU/RAM meters reduced to 56px: circular gauge with the percentage inside plus a thin linear bar; history sparkline removed.
- Toolbar Maximize/Restore button and smaller preview minimum size so the window can be resized.
- SkyStacker solve/sky-map/cutout argv now always points to the published blind catalog when available.
- Backend-only plate-solve failure confirmed by direct CLI: no local solvers and no consistent Gaia quad transform.

## 0.2.27 — 2026-11-19

- Fixed startup crash: `JobPanel` referenced an undefined `app` variable in `_build_layout`.
- Added a GUI smoke test that constructs `MainWindow` and verifies all dock panels.

## 0.2.26 — 2026-11-19

- RAW/DNG inspection with lossy-compression and Bayer/linear-DNG warnings.
- SER header parser and ffmpeg frame extraction for lucky-imaging sequences.
- AVI codec validation via ffprobe, rejecting lossy codecs such as MJPEG.
- Unit tests for the new format helpers.

## 0.2.25 — 2026-11-19

- Derivation tree dialog showing original, CLI operation chain and preview.
- Histogram phase 2 partial: shadow loupe and gamma slider mapped to ImageMagick `-evaluate Pow`.
- FITS compression adapters for fpack algorithms and gzip whole-file `.gz`.
- Unit tests for provenance, compression and gamma serialization.

## 0.2.24 — 2026-11-19

- Parameter suggestions from ISO/exposure metadata and frame quality diagnostics.
- Non-destructive annotations (label/arrow/circle) burned in via ImageMagick `-draw`.
- Linear-space guard blocks linear operations after non-linear stretch with optional override.
- Unit tests for presets, annotations and the guard.

## 0.2.23 — 2026-11-19

- Thumbnail strip for multiple open images and before/after difference map via ImageMagick.
- WCS overlay marking the plate-solution reference pixel on the canvas.
- Argv builders for RAW developers, Hugin, enfuse and GIMP with backend gating.
- Unit tests for the new adapters and WCS overlay conversion.

## 0.2.22 — 2026-11-19

- Direct ASTAP and solve-field adapters with RA/Dec seeds, scale hints and blind-scan warnings.
- Gaia cache management: configurable nside/cache path, offline mode and cache info dialog.
- Session save/resume with image list, stretch points and plate solutions.
- Unit tests for all three features.

## 0.2.21 — 2026-11-19

- Siril connector with calibration/stacking script generation and backend gating.
- Bad-pixel-map automation via SkyStacker with a 0.1% sanity cap.
- WCS values from plate solutions exported as `.wcs.json` sidecars beside FITS files.
- Unit tests for all three modules.

## 0.2.20 — 2026-11-19

- Visual job manager panel with per-job state, duration and retry using stored argv.
- Frame Table dialog measuring SNR/HFR/eccentricity/background via SkyStacker CLI.
- Case-insensitive calibration folder discovery (Bias/Dark/Flat/Light).
- Unit tests for job manager lifecycle, quality parser and calibration discovery.

## 0.2.19 — 2026-11-19

- Error dialogs show a short summary and a collapsible expander with full backend stderr.
- Mermaid architecture diagram, adapter docstrings, adapter checklist and known limitations added.
- Tests for corrupt settings, malformed histograms, Unicode names, cancellation and per-image undo; fixed two bugs found by them.

## 0.2.18 — 2026-11-19

- ImageMagick receives `-limit thread N` from the persisted thread setting.
- Operation log rotates by size with numbered JSONL backups.
- Batch conversion via `mogrify` with format and output-directory dialogs.
- Tests added for thread serialization, batch argv and log rotation.

## 0.2.17 — 2026-11-19

- Configurable accent colour (green/blue/orange/purple) applied to GTK CSS.
- File > Export Pipeline writes a shell script or Makefile with the exact recorded
  `argv`; `scripts/export_pipeline.py` offers the same for automation.
- Content-hash cache reuses TIFF transforms when input bytes and argv are unchanged.
- Unit tests added for pipeline quoting and cache reuse.

## 0.2.16 — 2026-11-19

- Main window is explicitly resizable/maximizable.
- Select Area button added to the toolbar with drag-to-select overlay and normalised
  rectangle helper.
- CPU/RAM meters halved in height (60px) while keeping gauge, history and core bars.
- Panel/toolbar labels now relabel live when the language changes; added unit and
  integration tests for selection, i18n coverage and recent-file actions.

## 0.2.15 — 2026-11-19

- Native wide-field blind plate solving via `--plate-solver native --blind-catalog mag07`,
  with automatic catalog discovery and `/usr/bin/env SKYSTACKER_CATALOGS=...` wrapper.
- Added Russian and Chinese translations and completed missing submenu/panel keys for
  all supported languages.
- File > Open Recent lists the 10 most recently opened images, persisted in settings.
- CPU/RAM indicators redesigned as circular gauges with 60-sample history sparklines
  and per-core bars, following the supplied visual reference.

## 0.2.14 — 2026-11-19

- Japanese (`ja`) added to the translator and the Frontend Settings language selector.
- Panel titles, dialog titles and status-bar messages are translated through the
  shared dictionary; GUI smoke verified Japanese menus and status output.

## 0.2.13 — 2026-11-19

- Settings now persist per-backend binary overrides, scratch root, Gaia cache directory
  and keyboard accelerators; BackendRegistry resolves overrides and SkyStacker receives
  `--gaia-cache-dir`.
- Default shortcuts extended and editable in Frontend Settings; changes apply immediately.
- Preview canvas accepts drag-and-drop of image files or folders (filtered by known
  astronomical extensions).

## 0.2.12 — 2026-11-19

- Canon CR2 input supported through SkyStacker's native pure-Go decoder:
  single-frame stack with `--tiff --no-postprocess`, producing a 32-bit float TIFF
  that becomes the working image; PNG preview is generated by the external CLI.
- SkyStacker input formats extended (CR2/CR3/SER/PGM/PPM/XISF) and Open requires
  SkyStacker for CR2. Unit tests cover argv and the workspace decode path.

## 0.2.11 — 2026-11-19

- Histogram handles now apply a throttled preview refresh after 1s of movement as well
  as immediately on release, capped at one CLI request per second.
- Fixed the backend detail window (Gtk.Entry has no `set_selectable()`), so a single
  click now opens the version/install dialog.
- Bottom progress strip CSS enlarged its text and removed borders so the status text
  and green progress share the same full-height widget.
- Roadmap format audit extended with Astro-TIFF, float planes, HDR formats, extended
  camera RAW lists, planetary MP4/MOV and modern web formats.

## 0.2.10 — 2026-11-19

- Histogram dock is visible from startup and filled automatically after open.
- Progress bar uses CSS so the whole 18px bottom strip is the indicator; status text is
  drawn inside it, and the separate status bar was removed.
- Translation dictionary expanded to submenus and dialog titles; Frontend Settings now
  owns language/theme/font, Backend Settings keeps connectors/offline/threads.
- Custom resize is a draggable Gtk.Window with a header bar.
- Roadmap audit items 6–8 completed: sanitized cleanup, UUID export fallback, stream close.

## 0.2.9 — 2026-11-19

- Backend click now opens a single detail window with copyable install/upgrade command;
  the apt-cache query message goes to the terminal log.
- The whole bottom strip is the progress bar (36px) with status text inside; a stopped
  job reports `Process stopped (OK)` instead of a workspace error.
- Metadata window reduced to 560x380. `cli_end` records include input/output byte sizes.
- Plate-solve failures confirmed as SkyStacker/backend limitations via direct CLI runs.

## 0.2.8 — 2026-11-19

- Backends panel shows green/red status icons; clicking a connector queries
  `apt-cache policy` and reports installed/candidate versions or the install command.
- All dialogs get a draggable header bar, including Resize image and format selection.
- Stop button restored on the toolbar (enabled only while jobs run); progress bar is
  40px tall and uses the full bottom width.
- Initial translation dictionaries for ES/DE/JA applied to menus, toolbar and key status
  messages; language changes take effect immediately.

## 0.2.7 — 2026-11-19

- SkyStacker bridge follows the current docs: `--image-op plate-solve` with
  `--plate-solver auto|gaia|astrometry-local|astap|astrometry-web`, scale hints,
  timeout and offline mode; layered SVG sky maps generated with `--image-op sky-map`.
- `plate_solution.json` is parsed into RA/Dec, pixel scale and FOV from WCS radians.
  Verified with the documented internal mock, which produced a layered SVG.
- Metadata PNG tab now reads the generated PNG (not the original file); Undo/Redo moved
  to the right of the toolbar; progress bar thickened; persistent application font size.
- Histogram computes automatically on open and View > Toggle Histogram Viewer controls
  its dock visibility.

## 0.2.6 — 2026-11-19

- Processing > Resize Image is now the scale submenu (10–1000% plus Custom Scale);
  the view-only Precise Scale submenu, 1:1 and Fit to Window entries were removed.
- Time model uses a conservative p75 seconds-per-megapixel, separates resize-up from
  resize-down, and the benchmark now includes a 300% case and keeps a display stretch on
  previews so end-to-end timings match real sessions.
- Progress bar is 16px high with text, pulses when no model exists and lingers at 100%
  with the actual duration before resetting. Estimate vs actual pairs are logged.

## 0.2.5 — 2026-11-19

- Roadmap expanded with the v0.2.3 audit findings: robustness fixes, test gaps,
  documentation contracts, thread propagation, log rotation and the first
  `MainWindow` refactor, ordered by difficulty.
- Desktop integration registers PSD/PSB, DNG, RAF, ORF, RW2, XISF and SER MIME types via
  a user-level shared-mime package, so Astro Studio appears in "Open With".

## 0.2.4 — 2026-11-19

- Histogram stretch is applied once per drag (on release) instead of on every mouse
  motion; handles now have bottom arrow grips and the chart draws filled distributions.
- Right-dock panel headers are half-height with smaller text and close buttons.
- Export format dialog is larger, draggable via a header bar and shows all formats at a
  glance with a smaller font.
- PSD/PSB import selects the flattened composite and applies a display stretch, fixing
  black re-opened PSDs.
- Benchmark extended to 20 MP; log/CSV/model regenerated with the larger cases.

## 0.2.3 — 2026-11-19

- Histogram is now a dock panel between CPU/RAM and Terminal; CLI output is bounded to
  256 colours on a 256px thumbnail, eliminating the multi-minute load.
- Two draggable cut-point handles on the histogram set low/high clipping via ImageMagick
  `-level`, regenerating only the preview PNG; the working TIFF stays untouched.
- CPU meter now exposes per-core saturation (`CPU 15% (core 98%)`) to explain single-core
  CLI loads; trough is dark, fill green below 75% and red at/above it (same for RAM).
- New export formats: PNG 16-bit, TIFF 32-bit float, FITS 32-bit float and flattened PSD.

## 0.2.2 — 2026-11-19

- CPU/RAM bars turn green below 75% and red at/above 75%.
- Terminal drawer uses a smaller monospace font and syntax-coloured tags for
  timestamps, commands, arguments, responses and errors.
- Histogram panel: CLI-generated distributions for the PNG preview and TIFF working
  file, logarithmic count axis, floating window with close button.
- Benchmark suite (opt-in) up to 10 MP appends timing data to the persistent operation
  log; analyzer script exports CSV and an incrementally updated proportionality model.
  The GUI shows estimated seconds and a green progress bar before each operation.

## 0.2.1 — 2026-11-19

- Rebuilt the GTK menu bar on dock state changes so View toggles visibly show
  `Backends Viewer: On/Off` and `Terminal Drawer: On/Off`.
- Metadata is now shown in a floating, closable window with the literal ExifTool output
  for both the PNG preview and the high-depth TIFF.
- Roadmap execution queue refined with immediate acceptance criteria and effort estimates.

## 0.2.0 — 2026-11-19

- Persistent operation log (JSONL) across sessions with CLI argv, duration, exit code
  and GUI events.
- CPU and RAM level indicators updated once per second via `psutil` with `/proc` fallback.
- Persistent preferences including enabled connectors, theme, language, offline mode and
  thread limit; GTK theme is actually applied.
- Dynamic On/Off labels for dock toggles, toolbar Undo/Redo, transform/export timing,
  active PNG/TIFF sizes in the status bar.
- Dual-format workspace with pan/zoom preservation, FITS RGB round-trip, Save As naming
  with incremental suffixes and Help > About.
- Extended ImageMagick filter submenus and SkyStacker astrometry bridge.

## 0.1.0 — 2026-11-18

- Initial architectural baseline: GTK 3.24 / PyGObject skeleton, CLI adapters,
  command builder, async process engine, scratch manager, tests and desktop packaging.
