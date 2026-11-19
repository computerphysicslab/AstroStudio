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
3. [ ] Verify the persistent operation log after a real open → filter → export cycle:
       entries must include `cli_start`, `cli_end`, duration and exit code, survive an
       application restart, and contain no image pixels. Effort: S.
4. [ ] Add `input_bytes`/`output_bytes` to `cli_end` records so the later time/memory
       estimator has file-size features. Effort: S.
5. [ ] Confirm CPU/RAM bars update within one second and the timeout is removed on
       window destruction. Effort: S.

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
      10 MP benchmark and analyzer producing CSV + incremental proportionality model;
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
8. [ ] Crop / rotate / flip / mirror option dialogs with internally generated flags
       (v0.2.0).
9. [x] Histogram phase 1: CLI-generated histogram text into a floating panel, logarithmic
       Y axis, preview vs working-TIFF distributions; pixel line profile still pending
       (v0.2.2).
10. [ ] Localization of interface strings (EN/ES/DE/JA) (v0.2.0).
11. [x] Small CPU/RAM level indicators using `psutil` with a `/proc` fallback, refreshed
       by `GLib.timeout_add()` in the right dock.
12. [ ] Extended export compression presets for already-installed backends: PNG 8/16-bit,
       JPEG quality + 4:4:4 subsampling, TIFF ZIP/LZW/PackBits/BigTIFF, FITS with the
       floating-point compression caveat documented in Context (v0.2.0).

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
22. [ ] PSD/PSB read-back via ImageMagick with explicit "flattened layers" warning
       (v0.3.0).

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
