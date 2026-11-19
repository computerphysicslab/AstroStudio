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
10. [x] Initial ES/DE/JA translation dictionary applied to menus, toolbar and key status
       messages (v0.2.8).

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

1. [ ] Extend Settings with binary overrides, scratch/cache directories and shortcut
       customization on top of the persisted connector/language/theme preferences (v0.2.0).
2. [ ] Complete keyboard shortcut set and shortcut customization (v0.2.0).
3. [ ] Drag-and-drop of files and folders onto the preview canvas (v0.2.0).
4. [ ] Dark theme CSS and configurable accent colours (v0.2.0).
5. [ ] Export pipeline as a reproducible shell script / Makefile using the exact
       serialized `argv` (v0.2.0).
6. [ ] Content-hash cache (input + parameters) to reuse prior artifacts (v0.2.0).
7. [ ] Batch conversion adapter (`gm mogrify` / `magick mogrify`) and dialog (v0.2.0).
8. [x] Resize percentages moved into Processing > Resize Image as a CLI submenu with
       Custom Scale; view-only Precise Scale removed (v0.2.6). Crop / rotate / flip /
       mirror option dialogs remain pending.
9. [x] Benchmark and estimator updated: p75 seconds/MP, separate resize-up/down,
       stretch-enabled preview timing and a visible lingering progress bar (v0.2.6).
9. [x] Histogram phase 1: CLI-generated histogram text in a dock between CPU/RAM and
       Terminal, logarithmic Y axis, preview vs working-TIFF distributions and two
       clickable/draggable low/high cut-point handles that trigger a CLI `-level` preview
       regeneration; pixel line profile still pending (v0.2.3).
10. [ ] Localization of interface strings (EN/ES/DE/JA) (v0.2.0).
11. [x] Small CPU/RAM level indicators using `psutil` with a `/proc` fallback, refreshed
       by `GLib.timeout_add()` in the right dock.
12. [x] Initial extended export formats via ImageMagick: PNG 16-bit, TIFF 32-bit float,
       FITS 32-bit float and flattened PSD. Remaining: JPEG 4:4:4 control, TIFF PackBits,
       BigTIFF and FITS tile-compression adapters (v0.2.3).
13. [ ] Propagate `settings.threads` to ImageMagick `-limit thread` and future adapters
       (v0.2.5).
14. [ ] Operation-log rotation/compaction by size/date plus `input_bytes`/`output_bytes`
       in `cli_end` records (v0.2.5).
15. [ ] Collapsible error dialog showing the relevant backend `stderr` in addition to the
       terminal drawer (v0.2.5).
16. [ ] Documentation: Mermaid architecture diagram, adapter `build_*_argv` contract
       docstrings, a "how to add an adapter" checklist and a known-limitations page
       (SkyStacker TIFF, FITS multi-HDU, display vs data stretch) (v0.2.5).
17. [ ] Unit-test gaps: scratch sanitization vs cleanup, histogram malformed lines,
       corrupt settings, Unicode/edge export names, process cancellation/timeouts and
       multi-image undo/redo (v0.2.5).

### Medium difficulty

1. [ ] Visual job manager: queue states, progress lines, retry, per-job timeouts and
       resource limits (v0.2.0).
2. [ ] Frame table with metadata and quality diagnostics (SNR, FWHM/HFR, eccentricity,
       background sigma, footprint) for culling (v0.3.0).
3. [ ] Case-insensitive calibration folder auto-detection and light-frame exclusion
       (v0.3.0).
4. [ ] Siril adapter: master dark/flat/bias from real frames and basic stacking with
       seeded alignment and affine guards (v0.3.0).
5. [ ] Bad-pixel-map automation with the 0.1% sanity cap (v0.3.0).
6. [ ] FITS/XISF header and WCS preservation on export where the backend supports it
       (v0.4.0).
7. [ ] Alternative plate solvers (ASTAP, `solve-field`) with explicit pointing seeds and
       blind-scan warnings; addresses the SkyStacker `0 matched pairs` failure (v0.4.0).
8. [ ] Gaia DR3 cache management at `nside=64` with offline/air-gapped mode (v0.4.0).
9. [ ] Session save/resume reusing scratch artifacts (v0.4.0).
10. [ ] Multi-document tabs, thumbnail strip and before/after slider or difference map
       via a delegated backend job (v0.2–v0.4).
11. [ ] WCS/catalog overlay on the canvas once a plate solution exists (v0.4.0).
12. [ ] RAW developers (RawTherapee/darktable/LibRaw), Hugin/enfuse and GIMP headless
       actions (v0.5.0).
13. [ ] Parameter suggestions/presets derived from image metadata and backend
       diagnostics (v0.5.0).
14. [ ] Non-destructive markup annotations (arrows, circles, labels) burned in only at
       export by GIMP/ImageMagick (v0.5.0).
15. [ ] Linear-space guard enforcement before non-linear stretching (v0.5.0).
16. [ ] Derivation tree view showing which original and operation chain produced the
       current image (v0.5.0).
17. [ ] Histogram phase 2: hybrid parametric + image-driven interface (v0.3.0):
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
18. [ ] FITS tile compression via external `fpack`/`funpack` adapters: RICE_1, GZIP_1/2,
       HCOMPRESS_1, PLIO_1, plus whole-file `.fits.gz`; avoid lossy float dithering
       unless explicitly requested (v0.3.0).
19. [ ] RAW/DNG connectors (RawTherapee, darktable, LibRaw) with explicit lossless-vs-lossy
       warnings and Bayer-vs-linear DNG handling (v0.3.0).
20. [ ] SER support via Siril/ffmpeg CLI for 8/16-bit uncompressed lucky imaging, with
       header Bayer pattern and per-frame timestamps preserved (v0.3.0).
21. [ ] AVI legacy capture support via ffmpeg with uncompressed/lossless codecs only;
       MJPEG rejected before stretching (v0.3.0).
22. [x] PSD/PSB read-back via ImageMagick `[0]` flattened composite with display stretch
       and an integration test (v0.2.4).
23. [ ] First `MainWindow` refactor: extract `MenuBuilder`, `ActionRegistry`,
       `DockManager` and reusable dialogs; keep behaviour identical (v0.3.0).
24. [ ] `mypy` strict on the core plus `pytest-cov` threshold (70% in `core/` and
       `adapters/`) in a pre-commit/CI job with `desktop-file-validate` (v0.3.0).
25. [ ] UI smoke tests with `pytest-gtk` that start the window and verify menus, dock
       toggles and metadata/histogram panels (v0.3.0).
26. [ ] SIGKILL escalation after a configurable per-job timeout to avoid zombie jobs
       (v0.3.0).
27. [ ] FITS multi-HDU detection with explicit errors instead of silent `-combine`
       failure on unusual files (v0.3.0).
28. [ ] Structured logging: standard Python logger mirrored into `OperationLog` instead
       of ad-hoc `_log()` strings (v0.3.0).

### High difficulty

1. [ ] Undo via operation replay / hardlinks with history depth policy instead of full
       TIFF+PNG copies (v0.3.0 target, research required).
2. [ ] Scalable previews: resolution pyramids, tiling and `GtkGLArea` rendering for
       very large FITS/stacks (v0.5.0).
3. [ ] Non-destructive visual pipeline graph: reorder, disable and duplicate nodes,
       exported as a reproducible script (v0.5.0).
4. [ ] Hot-folder watcher that triggers calibration + stacking when new lights appear
       (v1.0.0).
5. [ ] Smart catalog/HiPS prefetch for fully offline plate solving (v0.4.0).
6. [ ] Quality-validation dashboard after stacking/calibration using backend metrics
       (v1.0.0).
7. [ ] Plugin system with dynamic adapter registration via entry points (v1.0.0).
8. [ ] Remote compute adapters (SSH/API) for heavy stacking (v1.0.0).
9. [ ] Reproducible offline packaging (Flatpak/AppImage) with optional dependencies
       declared (v1.0.0).
10. [ ] Gradual GTK 4 migration once the runtime is available (post-v1.0.0).
11. [ ] XISF native read/write through an external CLI/library with LZ4/LZ4HC/Zlib/Zstd
       block compression, byte shuffling and checksum blocks (v0.5.0; no installed CLI
       covers this yet, so research is required).
12. [ ] BigTIFF (>4 GB) and Astro-TIFF keyword/WCS preservation end-to-end (v0.5.0).
13. [ ] Scientific validation dashboard for compression artefacts (banding from lossy
       RAW/JPEG/MJPEG before stretch, clipping counters, FWHM/SNR) (v1.0.0).

## Format coverage audit (reference)

| Format | Status via CLI | Notes / next step |
|---|---|---|
| FITS `.fits/.fit/.fts` | supported | First HDU or `-combine` import; 16/32-bit export |
| FITS tile compression `.fz`, GZIP_2 | planned | Needs `fpack`/`funpack` adapter (medium) |
| TIFF / BigTIFF | supported / planned | ZIP/LZW exported; BigTIFF needs `-define tiff:bigtiff` |
| XISF `.xisf` | planned | No installed CLI; research external reader/writer (high) |
| RAW `.cr2/.cr3/.nef/.arw/.raf/.orf/.rw2` | partially supported | Import via ImageMagick; RAW developers pending (medium) |
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

## Milestone mapping (reference only)

- **v0.2.0** — conversion/inspection completeness, settings persistence, job manager.
- **v0.3.0** — calibration, stacking and quality diagnostics.
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
