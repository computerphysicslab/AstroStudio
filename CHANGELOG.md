# Changelog

Version scheme: `MAJOR.MINOR.PATCH`.

- `MAJOR`: incompatible architecture or GUI stack change.
- `MINOR`: user-visible feature milestone (roadmap milestone completion).
- `PATCH`: each logical implementation, fix or tooling change.

Every implementation commit must bump `PATCH` at minimum and add an entry here.

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
