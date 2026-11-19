# Astro Studio — AI Project Context & Engineering Baseline

## 1. Project Identity & Core Mandate

* **Application Name:** Astro Studio
* **Platform & Toolkit:** Native Linux / Ubuntu desktop application built with **GTK 3.24** (GNOME standard) and GLib, implemented in **Python 3.8 with PyGObject** (`Gio.Subprocess` for async CLI execution). GTK4 is not available in the development environment.
* **Version:** `v0.2.5` (build 2026-11-19; see `CHANGELOG.md` and `roadmap.md` for milestone history)
* **Architectural Mandate (Zero-Processing GUI):**
  * Astro Studio is strictly a **decoupled, asynchronous desktop orchestration front-end**.
  * **No internal pixel manipulation:** The GUI codebase must **never** implement internal stacking, calibration, demosaicing, stretching, or mathematical image filtering algorithms.
  * **Pure CLI Orchestrator:** Astro Studio loads images from the local file system, renders them on screen, manages multi-format file I/O (e.g., opening `.jpg`, `.raw`, `.fits`, or `.tiff` and exporting/saving to `.png`, `.tiff`, `.jpg`, etc.), and translates user actions into sanitized command-line interface (`argv`) executions delegated to third-party open-source astronomical and photographic CLI engines.

---

## 2. High-Level Architecture & Subsystems

Astro Studio operates on an **Asynchronous Orchestration Pattern** layered over an **MVC / MVVM** structure:

1. **Presentation Layer (GTK UI):**
   * `GtkApplicationWindow` following GNOME Human Interface Guidelines (HIG).
   * **File Browser & Multi-Format Exporter:** Native `GtkFileDialog` and `GtkColumnView` to browse local captures, inspect metadata, and select target export formats.
   * **Preview Canvas (`GtkDrawingArea` / OpenGL / Vulkan):** High-performance display surface dedicated solely to rendering loaded input files and intermediate/final images written to disk by external CLI backends.
   * **Metadata & Terminal Drawers:** An on-demand ExifTool metadata panel (PNG and TIFF tabs) and a chronological CLI log (`argv`, timestamp, response and exit code). There is no Parameter Inspector: menus/option dialogs ask for intent and the GUI generates adapter flags internally.

2. **Command Builder & Adapter Pattern:**
   * Each external CLI binary is encapsulated inside an independent **Tool Adapter** defining supported input/output formats, default flag values, and argument serialization rules.
   * Arguments are built strictly as sanitized `argv` arrays—**never** concatenated into raw shell strings—preventing shell injection and handling file paths with spaces/special characters safely.

3. **Process Execution & Concurrency Engine:**
   * Built on GLib's event loop (`GMainContext`) using asynchronous process spawning (`g_spawn_async_with_pipes` or `Gio.Subprocess` / `asyncio` in PyGObject).
   * Never blocks the GTK UI thread during multi-minute external operations.
   * Parses `stdout`/`stderr` pipes asynchronously via regex/line readers to update GTK progress bars and logs, and supports explicit cancellation via `SIGTERM` / `SIGKILL`.

4. **Temporary Scratch Space & Cache Manager:**
   * Manages intermediate artifacts in a structured work directory (e.g., `<output>/_work/` or `/tmp/astro_studio/`), passing outputs sequentially between chained CLI tools and cleaning up ephemeral files on exit (unless preserved for `--resume` / session recovery).

5. **Startup Backend Discovery & Capability Gating:**
   * Immediately after activation, a `BackendRegistry` checks every connector binary with `shutil.which` and queries its version asynchronously through the same `ProcessEngine` (`magick -version`, `exiftool -ver`, `gm version`, etc.). No version query blocks the GTK thread.
   * Results (installed / not installed / version / error) populate only the GUI "Backends" panel, which has a close button and is restorable from *View > Toggle Backends Viewer*, and drive `Gio.SimpleAction` sensitivity: a menu item is enabled only if its adapter is implemented and at least one required backend is installed. Actions whose backend is missing stay visible but disabled and report the reason in the terminal log when clicked.
   * A binary that is installed but does not answer the version query remains "available" with version `unknown`; a missing binary disables its dependent actions.

---

## 3. Supported Third-Party Open-Source CLI Backends

Astro Studio delegates all format conversion, metadata reading, stacking, and post-processing to external Linux binaries installed on the host system:

### General Imaging, RAW & Metadata Connectors
* **RawTherapee (`rawtherapee-cli`):** 32-bit floating-point RAW development using `.pp3` profiles; exports to JPEG, PNG, and 8/16-bit TIFF.
* **Darktable (`darktable-cli`):** Headless RAW processing and format export using XMP sidecars and `.dtstyle` presets.
* **ImageMagick (`magick`):** Raster format conversion (e.g., JPG $\leftrightarrow$ PNG/TIFF/BMP), resizing, color-space conversion, and quick preview generation.
* **GraphicsMagick (`gm`):** High-speed multi-threaded batch format conversion (`gm mogrify`).
* **ExifTool (`exiftool`):** Read-only metadata extraction (`ExposureTime`, `ISO`, `FNumber`, `DateTimeOriginal`, FITS headers) to populate the UI inspector and session summaries without decoding pixel buffers in the GUI.
* **GIMP (`gimp -i -b`):** Headless Script-Fu / Python-Fu batch transformations.
* **Hugin (`pto_gen`, `cpfind`, `nona`, `enblend`):** Control-point alignment, remapping, and image stitching.
* **Enblend-Enfuse (`enfuse`):** Multi-exposure fusion (HDR) and focus stacking via exposure/contrast/saturation weights.
* **LibRaw (`dcraw_emu`):** Linear RAW sensor extraction with granular demosaicing and white-balance control.
* **PhotoFlow (`photoflow-cli`):** Non-destructive 32-bit floating-point `.pfp` filter pipeline execution.

### Dedicated Astronomical CLI Connectors (Recycled Domain Backends)
* **SkyStacker (`skystacker`):** Can be invoked as a headless calibration, registration, stacking, plate-solving, and 8-step post-processing backend (supporting `--calib-root`, `--self-flat-model=grid`, `--plate-solve`, `--drizzle-upsample`, `--starless`, `--deconvolve`, `--wavesharp`, and FITS/XISF/TIFF/PNG/JPEG outputs).
* **Siril (`siril-cli`), ASTAP (`astap_cli`), & Astrometry.net (`solve-field`):** Supported via the same Adapter pattern for plate solving, FITS calibration, and background extraction.

---

## 4. Recyclable Domain Rules & Scientific Guardrails (For CLI Adapters)

When Astro Studio builds UI panels, presets, or command pipelines for astronomical CLI backends, enforce these validated domain constraints:

1. **Calibration & Synthetic Refusal Guardrails:**
   * **Never fabricate synthetic bias, dark, or flat frames.** If a backend supports synthetic refusal flags (e.g., `--synthetic-dark/flat/bias`), do not expose fake-master generation in the UI.
   * **Auto-Detection of Calibration Layouts:** When scanning a session root folder, recognize standard calibration subdirectories case-insensitively (`Light`/`Lights`, `Dark`/`Darks`, `Flat`/`Flats`, `Bias`/`Biases`) and exclude calibration folders from light-frame discovery.
   * **Recoverable Metadata Defaults:** When real bias frames are absent, prefer metadata black-level pedestal subtraction (`--black-level auto` via EXIF `0x14A` or FITS `BLACK_LVL`). When real flats are absent and $\ge 15$ dithered lights exist, prefer sensor-space grid self-flatting (`--self-flat-model=grid`) over registered-space self-flatting (which absorbs extended nebulosity like M42).
   * **Dark-Series QA & Bad-Pixel Maps:** Support automated bad-pixel map generation (`--bpm-auto`) from master darks/biases with sanity caps (reject maps flagging $> 0.1\%$ of sensor pixels).

2. **Astrometry, Plate Solving & Gaia DR3 Cache:**
   * **Seeded Solving:** Always pass explicit pointing seeds to plate-solving adapters when available—prioritizing user UI coordinates (`--plate-center RA,DEC`) over FITS header `RA`/`DEC` keywords, and warning the user before attempting blind local scans.
   * **HEALPix Cache Awareness:** Default to `nside=64` ($\approx 0.84\text{ deg}^2$/tile) for local Gaia DR3 tile caches (`$XDG_CACHE_HOME/.../gaia_cache/`) to balance disk footprint and query speed; respect `--gaia-offline` modes in air-gapped environments.

3. **Registration, Resampling & Stacking Parameters:**
   * **Affine Overfitting Guards:** When configuring affine refinement in registration backends, enforce shear ($\le 0.10$) and anisotropy ($\le 1.10$) limits so noisy star fields do not collapse the valid crop footprint.
   * **Quality Weighting:** Surface frame diagnostics (`SNR`, `FWHM`/`HFR`, `Eccentricity`, `BgSigma`, `Foot%`) in the UI frame table so users can cull low-quality frames before invoking stacking commands.
   * **Nonlinear Guards for External AI Sidecars:** Tools performing linear-space operations (background extraction, deconvolution, star removal) must only be chained before non-linear histogram stretching (STF/MTF/Curves), unless the user explicitly overrides linear protection.

4. **Multi-Format Export & Preview Rules:**
   * Distinguish clearly in the UI between **scientific linear artifacts** (`.fits`, `.xisf`, `.f32raw`, 16/32-bit `.tiff`) and **display-stretched previews** (8-bit `.jpg`, `.png`, `.bmp` with gamma/percentile LUTs).
   * When converting formats via CLI tools (`magick`, `rawtherapee-cli`, `darktable-cli`), preserve EXIF/FITS WCS metadata headers whenever supported by the target format.

---

## 5. Non-Negotiable Engineering & Repository Constraints

* **Never Modify Original Input Files:** Source captures on disk are strictly read-only. All transformations write to user-specified export paths or isolated scratch directories (`_work/`).
* **No Blocking Calls on GTK Main Thread:** Every file discovery scan on large directories, EXIF batch read, and CLI tool execution must run asynchronously (`GTask`, `Gio.Subprocess`, or worker threads posting back via `GLib.idle_add`).
* **Contract Consistency (`UI` $\leftrightarrow$ `CLI Adapter` $\leftrightarrow$ `Tests`):**
  * Default values displayed in GTK widgets and tooltips **must** match the exact default flags serialized by the CLI Command Builder.
   * Every CLI Adapter must include automated unit/integration tests verifying `argv` serialization, missing-binary error handling (`ENOENT`), non-zero exit code recovery, and temporary file cleanup.
   * Every GUI menu/toolbar action must map to a CLI adapter as catalogued in `Context/GUI-specifications.md`; the GUI never implements the action's algorithm itself.
* **Build & Hygiene Discipline:**
  * Keep temporary backup files (`*.bak`), large local astrophotography datasets, and scratch `_work/` directories excluded in `.gitignore`.
  * Do not commit, push, or alter repository history unless explicitly instructed by the user.
  * Code, comments, identifiers, and technical documentation are written in **English**.

---

## 6. Local Test Datasets & Reference Paths (Do Not Commit)

For local integration testing of GTK file loading, metadata inspection, and CLI pipeline execution (always output test artifacts to `/tmp/astro_studio_*`, never inside source dataset directories):

* `assets/Orion-135mm/` — 66–67 $\times$ JPG (`2400x1600`), uncalibrated wide-field M42 session (useful for testing JPEG $\rightarrow$ PNG/TIFF conversion, ExifTool metadata tables, and grid self-flatting).
* `/home/jips/datos/Astro/datasets/OrionNebula/` — 134 CR2 lights, 22 darks, 17 flats, 5 biases (Canon EOS 40D; tests RAW handling and lowercase calibration folder auto-detection).
* `/home/jips/datos/Astro/datasets/04_emission_nebula_Flame/` — 45 FITS lights, 2 darks, 1 flat, 1 bias (`3056x2048`; tests FITS header parsing, RA/DEC extraction, and fast FITS pipelines).

---

## 7. Implementation Baseline (v0.1.0 — development started)

* **Source layout:** `astrostudio/` (GTK views, adapters, command builder, process engine, scratch manager), `tests/` (argv serialization and process lifecycle).
* **Entry point:** `python3 -m astrostudio`.
* **Phase 1 scope:** main window/menu/toolbar/status/log drawer, read-only image loading and preview, metadata inspection via `exiftool`, format export via the ImageMagick adapter, async process execution with cancellation and scratch cleanup, startup backend/version discovery with menu gating.
* **Modules created:** `astrostudio/app.py` (application, actions, discovery scheduling), `astrostudio/core/` (`command_builder.py`, `process_engine.py`, `scratch.py`, `backends.py`, `image_workspace.py`), `astrostudio/adapters/` (`base.py`, `magick.py`, `exiftool.py`), `astrostudio/ui/` (`main_window.py`, `preview.py`).
* **Backend availability at development time:** `exiftool` 11.88, GIMP 2.10.18 and ImageMagick 6.9.10 (`convert`; `magick` v7 absent) are detected at startup; the astronomical CLIs (Siril, ASTAP, etc.) are absent, so their actions are disabled rather than crashing or falling back to in-process processing. `AGENTS.md` at the project root records these standing rules.
* **Desktop integration:** `packaging/` holds the SVG icon, the `.desktop` template, the launcher script and a user-level `install.sh` that installs into `$XDG_DATA_HOME` (`~/.local/share`), refreshes caches and enables launching Astro Studio from the application menu (`gtk-launch astro-studio`). The desktop file was validated with `desktop-file-validate`.
* **User documentation:** `README.md` at the project root documents requirements, how to run the app, the automated test commands and the manual verification steps (including the ImageMagick export prerequisite).
* **Version control and planning:** the project is a Git repository; `roadmap.md` tracks milestones v0.1.0 through v1.0.0 with status tags matching the GUI specification. Commit each logical change, keep this context file and the roadmap updated in the same change, and never push or rewrite history without explicit user request.
* **Verification:** `python3 -m compileall -q astrostudio tests` and `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/` (60 passed, 1 opt-in benchmark skipped; pytest autoload is broken by an unrelated Dash plugin in this environment).

---

## 8. Dual-Format Image Invariant (v0.1.0)

* Every image opened by Astro Studio is stored in scratch as **two artifacts**: `working.tiff` (16-bit, maximum depth/colour, the sole input to external CLI transforms) and `preview.png` (8-bit display copy generated from the TIFF, the only file rendered by the GTK canvas).
* `ImageWorkspace.prepare()` creates both artifacts via external CLI; `transform()` runs the backend on the TIFF, atomically replaces it with the new TIFF (`os.replace`), then regenerates the PNG before the GUI reloads the preview. `export()` copies the PNG for `.png` targets or invokes the CLI from the TIFF for other formats. Original inputs are never modified.
* ImageMagick is accepted as `magick` (v7) or `convert` (v6); the adapter and the backend registry resolve either binary. The installed SkyStacker CLI cannot decode TIFF, so it is not used for the TIFF-to-PNG step in this baseline; the step is still performed by an external CLI, never in-process.
* The Metadata panel is filled by ExifTool with canonical tags (`-ExposureTime`, `-ISO`, `-FNumber`, `-DateTimeOriginal`, etc.) only when the (i) action is triggered, in two tabs (rendered PNG and working TIFF). Startup discovery resolves installed state synchronously before version queries so actions are enabled from the first frame.
* The preview canvas supports mouse-wheel zoom (read-only view transform).

---

## 9. Desktop Association and Export Catalog

* The `.desktop` entry declares `MimeType` for PNG, JPEG, TIFF, BMP, WebP, FITS, CR2, NEF and ARW, and uses `Exec=... %F`. The installer refreshes the desktop and MIME databases, so Astro Studio appears in Ubuntu's *Open With Other Application* list for images.
* `AstroStudioApplication` uses `Gio.ApplicationFlags.HANDLES_OPEN`; `do_open()` collects files passed by the file manager and `do_activate()` prepares each one through `ImageWorkspace`. `paths_from_command_line()` also handles raw argv paths.
* Export asks for the format **before** the destination. `astrostudio/core/export_formats.py` catalogs FITS 16-bit, TIFF 16-bit (uncompressed, LZW, Zip), PNG 8-bit, JPEG 8-bit (90%/95%) and BMP 8-bit with their CLI flags. The chosen extension is enforced; PNG copies the regenerated preview, all other formats are written from the TIFF by the external backend.
* Verified with `gio mime image/png` / `image/fits`, `desktop-file-validate`, a file-argument launch, and a real CLI export producing JPEG 60x60 from a resized TIFF.

---

## 10. View-Only Scale and Dialog-Driven Parameters

* The Parameter Inspector was removed. Users never type CLI flags: Processing > Resize Image asks for a percentage, Processing > Sharpen offers light/medium/strong presets, and Save As asks for the export format. The GUI maps those choices to `-resize`, `-unsharp` and format flags before spawning the backend.
* Processing > Precise Scale is a view-only submenu: 10%, 25%, 50%, 75%, 100%, 150%, 200%, 400%, 1000%, 1:1 (one screen pixel per image pixel) and Fit to Window. Double-clicking the preview (or the fit toolbar button) performs Fit to Window. These actions only change `PreviewPane` display state.
* Save As / Export asks for format first, then destination, and writes from the current working TIFF; it no longer performs a hidden transform. A cancelled dialog is reported in the log/status instead of failing silently.
* Verified with a GUI smoke: zoom levels apply, double-click restores fit, Save As writes a TIFF from the working TIFF, and 29 tests pass.

---

## 11. Dock Panels, CLI Log and Undo History

* The Backends panel has a close (X) button; *View > Toggle Backends Viewer* restores or hides it. The Metadata panel lives on the right with Backends and the Terminal Drawer, is hidden until the (i) metadata action is invoked, shows two ExifTool tabs (PNG preview and TIFF working), and also has a close button.
* The Terminal Drawer no longer repeats connector installation status. It logs each CLI call as `CLI <job-id> (<label>): <argv with date/time prefix>` followed by response lines and `CLI <job-id> exit <code>` (or a failure message). Backend status remains exclusively in the Backends panel.
* `ImageWorkspace` keeps per-image TIFF/PNG snapshots before each transform. `Edit > Undo / Redo` restores those snapshots and refreshes the canvas; menu sensitivity follows `can_undo()` / `can_redo()`. No external backend is invoked for history.
* The Cancel job toolbar button and action were removed; internal cancellation still runs on shutdown. Disabled actions now explain themselves in the terminal log instead of silently ignoring clicks (important for Save As).
* Verified with a GUI smoke: panels hide/restore, metadata tabs fill for PNG+TIFF, log contains CLI lines and no installation lines, undo/redo enable after a transform, and 31 tests pass.

---

## 12. Stable View, Dock Controls and Astrometry Bridge

* Transformations and Undo/Redo capture and restore `PreviewPane` zoom/fit plus scroll offsets, so applying a filter never changes the user's view state.
* The Metadata panel output is no longer echoed into the Terminal Drawer; the terminal auto-scrolls to the newest response. Both the Backends panel and the Terminal Drawer have close buttons and View-menu toggles (`toggle-backends`, `toggle-terminal`).
* Export/Actions report failures visibly (message dialog) and PNG export works without ImageMagick by copying the regenerated preview. The GTK application id was versioned to `org.astrostudio.gui.v2` so launches no longer get forwarded to stale single instances running older code.
* The new `Astrometry` menu bridges to the installed SkyStacker CLI: `--plate-solve --json-report` (with optional `--plate-center` seed) for field-of-view/plate solution, `--image-op sky-map` for a Gaia catalog SVG (converted to PNG by an external CLI), and `--image-op survey-cutout` for a HiPS FITS cutout. `astrostudio/core/astrometry.py` reads `plate_solution.json` and locates artifacts; all outputs go to scratch and failures are reported instead of fabricated. Real star fields and Gaia/HiPS access are required for meaningful results.
* Verified with GUI smokes: zoom 200% preserved across transform, metadata absent from terminal log, terminal toggle works, Save As writes TIFF, plate-solve argv is dispatched and its report is summarized; 35 tests pass.

---

## 13. Dock Ordering, Pan, Open Filters and Working Astrometry

* The Backends panel sorts installed connectors first (alphabetical by name), then missing ones.
* `PreviewPane` supports left-drag panning (`start_pan`/`update_pan`/`end_pan`) in addition to wheel zoom and double-click fit. Pan offsets are captured with zoom/fit/scroll in `MainWindow._capture_view_state()` and restored after transforms, Undo and Redo.
* The Open dialog registers upper- and lowercase patterns for PNG, JPEG, TIFF, FITS, BMP, CR2/CR3, NEF, ARW, DNG, XISF plus an "All files" filter, and explicitly sets the image filter (GTK filters are case-sensitive on Linux).
* **Save As bug fixed:** `Gtk.ScrolledWindow` has no `set_min_content_size()` in GTK 3.24; the format dialog now uses `set_min_content_width/height`. Verified with a real-dialog smoke that selects TIFF, chooses a destination and writes the export.
* Astrometry: SkyStacker only invokes its WCS solver from `--image-op sky-map` or `survey-cutout`. `measure-quality` produced `image_measurements.json` (not a plate solution), which caused the false "OK". Plate Solve now uses the WCS-capable op, writes `<base>_plate_solution.json`, normalises/caches it as `plate_solution.json`, and Sky Map / Survey Cutout copy that cached solution into their scratch output before running. Failures are surfaced as errors.
* Verified with GUI smokes: pan (60,30) preserved across transform, Save As via real dialogs writes TIFF, plate-solve dispatches the corrected argv and reports the backend error; 36 tests pass.

---

## 14. UX Feedback, FITS Preview and Plate-Solve Diagnosis

* A busy `watch` cursor is set from job dispatch until the final `on_done`/error callback for image import, transforms, export, metadata and astrometry; `MainWindow._busy_begin()`/`_busy_end()` use a counter so concurrent jobs do not clear it early.
* `toggle-backends` and `toggle-terminal` are now in `IMPLEMENTED_ACTIONS`, so the View menu entries stay enabled after their panels are closed with the X button.
* FITS import uses the CLI selector `file.fits[0]` to take the first HDU; FITS/RAW sources set `WorkingImage.display_stretch`, so `build_preview_argv()` adds ImageMagick `-evaluate Pow 0.45` when regenerating the display PNG. Scientific exports stay linear. Verified on `assets/IMG_4062_processed.fits`: preview mean went from ~7 to ~49 (visible).
* Plate-solving diagnosis: the exact same SkyStacker command run directly outside AstroStudio reproduces `plate solve: no consistent transform (0 matched pairs)`, so the failure is in the backend's star matching / catalog data, not in AstroStudio's argv or UI. The JPG has no RA/DEC EXIF tags (only camera/date/focal length), so no reliable header seed is available; blind solving and an M42 seed with higher Gaia magnitude limit both failed. AstroStudio now reports the real error; alternative solvers (ASTAP, `solve-field`) are on the roadmap.
* `roadmap.md` was reorganised: completed v0.1.0 baseline first, then the pending backlog ordered by difficulty (low → medium → high) with milestone tags and the audited feature ideas (pipeline-as-code, job queue, thumbnails, before/after, derivation tree, hot-folder, plugins, remote compute, GTK 4).

---

## 15. Persistent Preferences, Export Naming, Filters and Histogram Plan

* `SettingsManager` persists user preferences as JSON under `$XDG_CONFIG_HOME/astro-studio/settings.json`: installed-connector on/off state, language, theme, offline mode and thread limit. `BackendRegistry.available()` now requires both installation and the user-enabled flag, while `installed()` reports the physical state. *Options > Backend Settings* opens a dialog with checkboxes for installed connectors plus the other preferences; saving persists them for later sessions.
* Save As suggests the current image name with the chosen format's extension (no `_processed` suffix). `unique_export_path()` appends `-1`, `-2`, `-3`, ... before the extension only when the exact destination already exists. The status bar reports `Export complete: name (X.XX MB, Y.Y s)` using file size and monotonic elapsed time.
* FITS colour round-trip fixed: ImageMagick writes RGB FITS as three grayscale HDUs, so import now uses `convert file.fits -combine -depth 16 ...`; a real-CLI integration test verifies that an RGB PNG exported to FITS and re-imported remains RGB.
* The Filter menu now has recursive submenus (Sharpen / Smooth & Denoise / Convolution & Morphology / Astronomical) with more than ten ImageMagick-backed operations (blur, gaussian blur, median, despeckle, adaptive blur, sharpen, convolve, morphology, edge, emboss, star-size reduction); all are generated as flags by the GUI and run on the working TIFF.
* Histogram design (analysis requested; implementation planned under the v0.2.0 roadmap item):
  1. Add a docked Histogram panel fed by CLI text (`convert <preview> histogram:`), never by GUI pixel math; show the current display stretch (none for PNG/JPEG, `-evaluate Pow 0.45` for FITS/RAW) in the legend.
  2. Make the stretch an explicit per-image setting (`display_stretch` already exists on `WorkingImage`) and display raw vs displayed histograms side by side.
  3. Clicking/dragging on the histogram selects a stretch preset (gamma/black point), which is converted into an ImageMagick flag and triggers a fresh CLI preview job; the canvas and histogram refresh together.
  4. Cache histogram/preview results by content hash and keep scientific exports linear; later extend to backend-provided asinh/STF stretches when a TIFF-capable backend is available. See `Context/GUI-specifications.md` and the CLI-generated histogram roadmap item.

---

## 16. Theme, Toggle Labels, Filter Fixes and Resource Monitors

* The persisted `theme` preference is now applied through `Gtk.Settings`: `dark` uses Yaru-dark/Adwaita-dark with `gtk-application-prefer-dark-theme=True`, `light` uses Yaru-light/Adwaita, and `system` restores the startup values. Verified in a GUI smoke (Yaru -> Yaru-dark -> Yaru-light -> Yaru).
* View menu items for dock panels are stored as `Gio.MenuItem` objects and relabelled `Toggle <panel> On/Off` from panel visibility, including when the X button is used. Toolbar Undo/Redo buttons were added; both actions are already sensitivity-gated by workspace history.
* Transform and export status lines include elapsed seconds; the status line always reports the active image's PNG and TIFF sizes in MB after open, transform and history operations.
* Filter fixes: `CommandBuilder` formatters may expand one flag into several `argv` tokens, so `-morphology Erode Disk:1` is correct; `-edge` and `-emboss` now pass radius `1` (ImageMagick 6 requires an argument). Star-size reduction reuses the morphology operation. The duplicate Processing > Sharpen entry was removed (Sharpen remains in the Filter submenu).
* Added Help > About with version, build date and project description via `Gtk.AboutDialog`.
* CPU/RAM indicators are implemented in `astrostudio/ui/resource_monitor.py`: two `Gtk.LevelBar`s in the right dock updated every second from `psutil` (5.8.0 installed) with a pure `/proc/stat` + `/proc/meminfo` fallback. Helpers `parse_meminfo`, `parse_proc_cpu` and `cpu_delta` are unit-tested. This reads system state only (no image pixels), so it does not breach the zero-processing mandate.

---

## 17. Persistent Operation Log, Format Catalog and Version Policy

* `OperationLog` appends newline-delimited JSON to `$XDG_DATA_HOME/astro-studio/operations.jsonl` and is never truncated. `ProcessEngine` records `cli_start`/`cli_end` with job id, argv, duration, exit code and stderr summary (backend version probes are excluded); the GUI also records `session_start`, `open_requested` and `export_requested`. Data is intended for later time/memory estimation of operations.
* Menu toggle labels now force a `Gio.Menu.items_changed()` emission after `Gio.MenuItem.set_label()`, so On/Off state propagates to the GTK menu bar. Verified in a GUI smoke.
* Version is `0.2.0` (build 2026-11-19). Policy: `MAJOR.MINOR.PATCH`; every implementation commit bumps `PATCH` at minimum and adds a `CHANGELOG.md` entry. `MINOR` marks roadmap milestones. This supersedes the earlier 0.1.0 baseline label.
* Roadmap now incorporates the format survey (FITS tile compression variants and `.fits.gz`, XISF LZ4/Zstd + byte shuffle, TIFF ZIP/LZW/BigTIFF/Astro-TIFF, RAW/DNG compression caveats, SER/AVI uncompressed-only rules, PSD/PSB, PNG/JPEG presets) with explicit CLI connectors and difficulty ordering.
* Roadmap histogram design now follows the hybrid model: dual overview + shadow-loupe view, logarithmic Y / zoomable X axes, parametric GHS/Asinh handles, direct canvas click-to-anchor, STF-vs-data-stretch decoupling, clipping guardrails and a non-destructive stage stack. Bezier curves are deferred until after the image is non-linear.

---

## 18. v0.2.1 — Dock Labels and Metadata Window

* GTK 3.24 does not repaint GMenu text after `Gio.MenuItem.set_label()`, so `MainWindow._rebuild_menu_bar()` now rebuilds the whole `Gtk.MenuBar` whenever a dock visibility changes. View entries read `Backends Viewer: On/Off` and `Terminal Drawer: On/Off`, verified in a GUI smoke after both the X button and the View action.
* The (i) Metadata action now opens a floating `Gtk.Window` with a `Gtk.HeaderBar` close (X) button and a two-tab `Gtk.Notebook` showing the **literal** ExifTool output for the PNG preview and the working TIFF. The two CLI jobs are tracked with `metadata_pending`, and the window opens once both finish; the docked metadata panel remains as a secondary view.
* Version bumped to `0.2.1` with a `CHANGELOG.md` entry, and `roadmap.md` gained a "Current execution queue (next 30 minutes)" section with acceptance criteria for the dock labels, metadata window, operation-log validation and resource-monitor checks.

---

## 19. v0.2.2 — Ergonomics, Histogram and Time Estimation

* `ResourceMonitor` applies CSS so bars and labels are green below 75% usage and red at/above 75%, using `Gtk.LEVEL_BAR_OFFSET_HIGH`.
* The Terminal Drawer uses monospace 8 and `Gtk.TextBuffer` tags: timestamp (grey), command label (blue), program (purple), arguments (yellow), responses (light grey), success (green) and errors (red). `log_segments()` is a pure, unit-tested classifier.
* Histogram phase 1 is implemented: `parse_histogram_text()` reads ImageMagick `histogram:info:-` output, `HistogramWidget` draws two overlaid 0–255 distributions with a logarithmic count axis, and a floating closable window shows the displayed PNG and the working TIFF.
* `tests/benchmark_operations.py` (opt-in, max 10 MP) opens, filters and exports images, appending timed events to the persistent log. `scripts/analyze_operations.py` exports `operations.csv` and incrementally updates `estimates.json` with sufficient statistics per stage (`seconds = slope * megapixels + intercept`). Both were executed: 648 new log entries, 11 modelled stages.
* `Estimator` feeds the GUI: before open/transform/export the status bar shows the estimated seconds and a full-width green `Gtk.ProgressBar` fills over that duration. Verified with a GUI smoke using an injected model.
* Version is now `0.2.2` with the corresponding `CHANGELOG.md` entry.

---

## 20. v0.2.3 — Fast Histogram Dock, Stretch Handles and More Formats

* The histogram is now a closable dock panel between CPU/RAM and Terminal instead of a floating window. `histogram_argv()` bounds the CLI work with `-resize 256x256! -colors 256`, so the chart appears in about a second instead of minutes even for large TIFFs; a real GUI smoke confirmed two datasets and a fast refresh.
* `HistogramWidget` exposes two draggable cut-point handles. Releasing/dragging calls `_on_stretch_change()`, which stores the points on `WorkingImage` and asks `ImageWorkspace.update_preview()` to regenerate only `preview.png` with ImageMagick `-level low%,high%`. The 16-bit TIFF is never modified; zoom/pan are restored after the refresh.
* CPU analysis: `psutil.cpu_percent(interval=None)` reports system-wide usage (one saturated core on an 8-core machine reads ~12–15%), which explained the apparently wrong indicator. The bar now uses `max(overall, peak core)` and the label reads `CPU <overall>% (core <peak>%)`, so single-threaded CLI load is visible. CSS sets a dark trough, green fill below 75% and red at/above, with the same rule for RAM.
* Export catalog gained PNG 16-bit, TIFF 32-bit float, FITS 32-bit float and flattened PSD; the Open filter accepts PSD/PSB. XISF/SER/AVI remain roadmap items because no installed CLI covers them.
* Version bumped to `0.2.3` with a `CHANGELOG.md` entry.

---

## 21. v0.2.4 — Dock Ergonomics, PSD and 20 MP Benchmark

* `HistogramWidget` now emits its stretch callback only on button release, so a drag
  produces exactly one CLI `-level` job (verified with a synthetic drag smoke). Handles
  have bottom arrow grips and a wider hit zone; the chart draws filled distributions
  plus bars and an explicit message when no data is available.
* Right-dock headers use `sans 9`, a 16px high box and a flat 16x14 close button, roughly
  halving their vertical footprint. Order is fixed: CPU/RAM monitor, Backends, Metadata
  (hidden by default), Histogram, Terminal Drawer.
* The export format dialog has a `Gtk.HeaderBar` (draggable), 600x560 default size, 520x480
  scroll area and `Sans 9` rows so all formats are visible at once.
* PSD/PSB import uses the `[0]` composite selector and a CLI display stretch; a real-CLI
  integration test verifies an RGB PNG survives a PSD round trip with visible colour.
* Benchmark limit raised to 20 MP (5000x4000 case). Re-run produced 1211 new log entries,
  a 715-row CSV and 11 stage models with doubled sample counts.
* **Right panel rule:** this dock state section must be refreshed on every iteration so
  the opencode right panel never shows stale panel visibility/order.

---

## 22. v0.2.5 — Audit Backlog and Extended MIME Registration

* The v0.2.3 audit findings were added to `roadmap.md` while keeping the difficulty
  order: low (cleanup sanitization, export-name fallback, stream closing, thread
  propagation, log rotation/bytes, error dialog, documentation contracts, unit-test
  gaps), medium (first `MainWindow` refactor, mypy/coverage CI, UI smoke tests, SIGKILL
  escalation, FITS multi-HDU detection, structured logging) and the existing high
  tier (hardlink undo, pyramids, plugin system, GTK 4).
* Desktop registration now includes `image/vnd.adobe.photoshop` (plus the `x-psd`
  alias), DNG/RAF/ORF/RW2, XISF and SER MIME types. A user-level shared-mime XML adds
  `*.psb`, `*.xisf` and `*.ser` globs; `install.sh` installs it and refreshes the MIME
  database. Verified with `gio mime image/vnd.adobe.photoshop`: Astro Studio is both
  registered and recommended for PSD.
* Canonical version line at the top of this document now tracks the current release
  rather than the original v0.1.0 baseline.