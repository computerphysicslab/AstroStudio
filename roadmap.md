# Astro Studio Roadmap

This roadmap tracks delivery of the zero-processing GTK orchestrator described in
`Context/AstroStudio_ai_project_context.md`. Status tags match the action tags in
`Context/GUI-specifications.md`: **[P1]** implemented, **[P2]** adapter/UI pending,
**[P3]** planned.

Non-negotiable rules for every milestone: no pixel math in the GUI, `argv` arrays
only, asynchronous subprocesses, scratch-only intermediate files, original inputs
read-only, and tests for every adapter.

## v0.1.0 — Foundation (current, in progress)

- [x] Coherent specifications: GUI actions are CLI delegations through scratch files.
- [x] GTK 3.24 / PyGObject application skeleton with menu bar, toolbar, status bar,
      read-only preview canvas, metadata panel and terminal drawer.
- [x] Sanitized `CommandBuilder` (ordered flags, booleans, formatters, NUL rejection).
- [x] Async `ProcessEngine` with line-streamed stdout/stderr, exit codes and `SIGTERM`
      cancellation.
- [x] Scratch manager under `XDG_RUNTIME_DIR` / `/tmp`, with job cleanup.
- [x] First adapters: ImageMagick (export/resize/unsharp/crop/rotate) and ExifTool
      (metadata inspector).
- [x] Startup backend discovery: installed/version status for every connector, shown
      in the Backends panel, driving `Gio.SimpleAction` menu sensitivity from the
      first frame (installed state resolved before version queries).
- [x] Dual-format workspace: each opened image gets a 16-bit working TIFF and a PNG
      preview in scratch; every transform runs on the TIFF via external CLI, replaces
      it, and regenerates the PNG that the GUI renders.
- [x] Metadata panel populated automatically by ExifTool on open and refreshed by the
      (i) button/toolbar action, with canonical EXIF/FITS tags.
- [x] Desktop/MIME registration for image types and command-line file opening from
      the file manager ("Open With Other Application").
- [x] Export format picker shown before Save As: FITS, TIFF 16-bit (uncompressed,
      LZW, Zip), PNG, JPEG (90/95%), BMP.
- [x] Double-click on the canvas (and the fit button) performs Fit to Window;
      Processing > Precise Scale provides 10/25/50/75/100/150/200/400/1000%, 1:1 and
      Fit to Window as view-only zoom levels.
- [x] Parameter Inspector removed: the GUI generates CLI flags from menu/dialog
      choices (resize percentage, sharpening preset, export format).
- [x] Backends panel with close button and *View > Toggle Backends Viewer*; on-demand
      Metadata panel on the right with PNG/TIFF tabs and its own close button.
- [x] Terminal Drawer logs timestamped CLI `argv` plus responses/exit codes instead of
      repeating backend installation status.
- [x] Real Undo/Redo of TIFF+PNG snapshots after a transform; Cancel job button removed.
- [x] Test baseline: argv serialization, adapters, scratch isolation, process
      lifecycle (ENOENT/exit code), discovery gating.
- [x] Git version control initialized on `main` with an initial commit.
- [x] Desktop integration: SVG icon, user-level installer, `.desktop` entry and launcher script.

## v0.2.0 — Conversion and inspection completeness

- [x] Mouse-wheel zoom control on the preview canvas.
- [ ] Batch conversion adapter (`gm mogrify` / `magick mogrify`) and batch dialog.
- [ ] Crop/rotate/flip/mirror options exposed as dialogs with internally generated flags.
- [ ] CLI-generated histogram view and pixel line profile (text output parsed by GUI).
- [ ] Frame table with metadata columns and quality diagnostics (SNR, FWHM/HFR,
      eccentricity, background sigma, footprint) for culling.
- [ ] Backend settings dialog: binary overrides, scratch/cache directories, thread
      limits, offline mode.
- [ ] Localization of interface strings (EN/ES/DE/JA).

## v0.3.0 — Calibration and stacking

- [ ] Siril / SkyStacker adapters for master dark, flat and bias generation from real
      frames only; synthetic masters never exposed.
- [ ] Case-insensitive calibration folder auto-detection and light-frame exclusion.
- [ ] Registration and stacking pipelines with seeded alignment, affine shear <= 0.10
      and anisotropy <= 1.10 guards.
- [ ] Bad-pixel-map automation with sanity caps (reject maps flagging > 0.1% pixels).
- [ ] Scientific linear artifacts (`.fits`, `.xisf`, 16/32-bit TIFF) kept distinct from
      display-stretched previews.

## v0.4.0 — Astrometry and scientific export

- [ ] Plate solving through `solve-field` / ASTAP with explicit pointing seeds
      (user coordinates first, FITS RA/DEC second) and blind-scan warnings.
- [ ] Gaia DR3 tile cache at `nside=64`, with offline/air-gapped support.
- [ ] FITS/XISF header and WCS preservation in exported files where supported.
- [ ] Optional `--resume` session recovery preserving scratch artifacts.

## v0.5.0 — Extended backends and pipelines

- [ ] RAW developers (RawTherapee `.pp3`, darktable XMP), LibRaw and PhotoFlow `.pfp`
      pipeline execution.
- [ ] Hugin tools (`pto_gen`, `cpfind`, `nona`, `enblend`) and `enfuse` fusion.
- [ ] GIMP headless Script-Fu/Python-Fu actions (clone stamp, custom macros).
- [ ] Magnetic/linear guard enforcement: background extraction, deconvolution and star
      removal chained only before non-linear stretch unless explicitly overridden.

## v1.0.0 — Release

- [ ] Full menu/toolbar coverage according to `Context/GUI-specifications.md`.
- [ ] Integration runs against the local Orion, CR2 and FITS datasets referenced in the
      context file, with artifacts written only to `/tmp/astro_studio_*`.
- [ ] Documentation, packaging and a stable Python/GTK dependency declaration.

## Version-control practice

- `main` is the integration branch; commit each logical change with a concise message
  in English.
- Keep `Context/AstroStudio_ai_project_context.md` updated in the same change as any
  code, structure, spec or tooling modification, and update this roadmap when status
  changes.
- Never commit scratch files, backups, large datasets or secrets; `.gitignore` excludes
  generated caches.
- No push, tag, merge or history rewrite without explicit user request.
