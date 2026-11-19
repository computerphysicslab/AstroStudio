# Changelog

Version scheme: `MAJOR.MINOR.PATCH`.

- `MAJOR`: incompatible architecture or GUI stack change.
- `MINOR`: user-visible feature milestone (roadmap milestone completion).
- `PATCH`: each logical implementation, fix or tooling change.

Every implementation commit must bump `PATCH` at minimum and add an entry here.

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
