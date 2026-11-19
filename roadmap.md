# Astro Studio Roadmap

This roadmap tracks delivery of the zero-processing GTK orchestrator described in
`Context/AstroStudio_ai_project_context.md`. Status tags match the action tags in
`Context/GUI-specifications.md`: **[P1]** implemented, **[P2]** adapter/UI pending,
**[P3]** planned.

Non-negotiable rules for every item: no pixel math in the GUI, `argv` arrays only,
asynchronous subprocesses, scratch-only intermediate files, original inputs read-only,
and tests for every adapter. The pending backlog is ordered by difficulty, easiest
first; the milestone tags are a reference for release planning only.

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
      operations (blur, denoise, convolution, morphology, star-size reduction).
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
9. [ ] CLI-generated histogram view and pixel line profile (v0.2.0). Phased design is
       documented in `Context/AstroStudio_ai_project_context.md`: CLI text histogram,
       raw vs displayed stretch, clickable stretch presets converted to CLI flags.
10. [ ] Localization of interface strings (EN/ES/DE/JA) (v0.2.0).

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
