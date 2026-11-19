# Changelog

Version scheme: `MAJOR.MINOR.PATCH`.

- `MAJOR`: incompatible architecture or GUI stack change.
- `MINOR`: user-visible feature milestone (roadmap milestone completion).
- `PATCH`: each logical implementation, fix or tooling change.

Every implementation commit must bump `PATCH` at minimum and add an entry here.

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
