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
* ImageMagick is accepted as `magick` (v7) or `convert` (v6); the adapter and the backend registry resolve either binary. SkyStacker now decodes TIFF through its first-party goTiff module and can be used directly on the 16-bit working TIFF for image-op jobs; the TIFF-to-PNG preview step remains an external ImageMagick CLI job, never in-process.
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
* Processing > Resize Image is a CLI-action submenu: 10%, 25%, 50%, 75%, 100%, 150%, 200%, 400%, 1000% plus Custom Scale; each resizes the working TIFF and regenerates the preview. Double-clicking the preview (or the fit toolbar button) performs Fit to Window as a view-only action.
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
  halving their vertical footprint. Current order: CPU/RAM monitor, Backends, Metadata
  (hidden by default), Histogram, Jobs and Terminal Drawer; Jobs was added later and is
  visible by default.
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

---

## 23. v0.2.6 — Resize Submenu and Trustworthy Estimates

* Processing > Resize Image now owns the scale choices (10–1000% plus Custom Scale) as
  real CLI transforms. The view-only Precise Scale submenu and its 1:1 / Fit to Window
  entries were removed; Fit to Window stays in View and double-click.
* Estimation analysis from the log: a 300% resize estimated ~0.3 s actually took 3.66 s,
  and a star-reduction estimated 3 s took 9.6 s because 3.86 s went to the transform and
  5.74 s to regenerating the stretched PNG preview. The benchmark now keeps a display
  stretch on previews and includes a 300% resize case, so end-to-end timings are measured.
* `scripts/analyze_operations.py` now uses the 75th percentile of seconds/megapixel per
  stage instead of least squares, avoiding systematic underestimation on slower code
  paths. Models are versioned (v2); resize-up and resize-down have separate slopes.
* The progress bar is 16 px high with text, pulses when no model is available, fills to
  100% with "Done in X s" and lingers 1.2 s before resetting. `estimate` and
  `estimate_result` events are appended to the persistent operation log for later
  accuracy analysis.
* Version bumped to `0.2.6` with a `CHANGELOG.md` entry.

---

## 24. v0.2.7 — Current SkyStacker Contract and UI Fixes

* Documentation reviewed from `SkyStacker/docs/` (plate-solving, astrometry-products,
  integration, output-formats). Key corrections: use `--image-op plate-solve` (not
  `measure-quality`), choose `--plate-solver auto|gaia|astrometry-local|astap|astrometry-web`,
  pass `--astrometry-timeout`, optional `--solver-focal-length`/`--solver-pixel-size`,
  and `--gaia-offline` from settings. Standalone products are
  `<base>_plate_solution.json` and a layered `<base>_sky_map.svg`.
* `astrostudio/core/plate_solution.py` converts WCS CRVAL (radians), CD determinant and
  image dimensions into RA/Dec, arcsec/px and FOV degrees. The GUI shows this summary
  after a successful solve. A direct CLI run reproduced the documented failure chain
  (seeded Gaia 0 matches → no local solver → no API key), confirming the bridge reports
  real backend results. The documented internal mock produced a 30-source layered SVG.
* Histogram is computed automatically after each image is prepared; View > Toggle
  Histogram Viewer shows/hides its dock with an On/Off label. The PNG metadata tab now
  reads the generated preview PNG, Undo/Redo are at the right end of the toolbar, the
  progress bar is 24px high, and a persisted `font_size` preference resizes the GTK UI.
* Version bumped to `0.2.7` with a `CHANGELOG.md` entry; format coverage audit added to
  the roadmap.

---

## 25. v0.2.8 — Backend Details, Movable Dialogs and Stop Button

* Backends panel now shows a green `dialog-ok` / red `dialog-error` icon before each name.
  Activating a row queries `apt-cache policy <package>` asynchronously (job id prefixed
  `probe-`, excluded from the operation log) and opens a movable dialog with detected,
  installed and candidate versions plus the exact `sudo apt install ...` command when
  missing or upgradable. `core/package_info.py` owns the binary→package map and parser.
* Log diagnosis for the reported astrometry failures: plate solve, sky map and survey
  all exited 1 because no `--plate-center` seed was supplied and the auto chain found
  no local `solve-field`, no ASTAP and no `AN_API_KEY`; sky-map/survey additionally need
  a `plate_solution.json`. Astro Studio now surfaces these real backend errors.
* All subwindows use `Gtk.HeaderBar` plus `window_utils.make_draggable()` (export format,
  custom resize, sharpen, metadata, info/error, plate options, settings, generated map).
  The Stop button is back in the toolbar and enabled only while `engine.active_jobs` is
  non-empty; it sends SIGTERM through `ProcessEngine.cancel()`.
* Progress bar is 40px high, full width, with text and a 1.2s linger at 100%.
* `core/i18n.py` holds an extensible ES/DE/JA dictionary; menus, toolbar labels and key
  status messages switch immediately when Options > Backend Settings saves a new language.
* Version bumped to `0.2.8` with a `CHANGELOG.md` entry.

---

## 26. v0.2.9 — Single Backend Dialog and Bottom Progress Strip

* Clicking a backend now opens one dialog only. The `apt-cache` query is logged in the
  Terminal Drawer; the detail window shows detected/installed/candidate versions and an
  `Gtk.Entry` with the copyable `sudo apt install ...` command plus a Copy button using
  `Gtk.Clipboard`. Metadata window reduced to 560x380.
* The separate status bar was removed; the bottom strip **is** the `Gtk.ProgressBar`
  (36px, full width, text inside). `_status()` writes into its text and the 100% linger
  restores the last status message afterwards.
* Cancellation is explicit: `ProcessHandle.cancelled` makes the engine report
  `cancelled by user`, and `MainWindow._on_workspace_error()` answers with
  `Process stopped (OK)` instead of an error dialog.
* `cli_end` records now carry `input_bytes` and `output_bytes`. The three pending
  audit-queue items (log validation, byte fields, CPU/RAM timer cleanup) are complete.
* Plate solving diagnosis confirmed against the real log and direct CLI: the auto chain
  has no seed, no local `solve-field`/ASTAP and no `AN_API_KEY`; seeded Gaia matching on
  processed JPEGs yields `0 matched pairs`. This is a SkyStacker/backend limitation,
  not a GUI argv bug; Astro Studio surfaces the exact backend error.
* Version bumped to `0.2.9` with a `CHANGELOG.md` entry.

---

## 27. v0.2.10 — Histogram on Startup and Frontend Settings

* Histogram dock is no longer `no_show_all`; it is visible at startup and `action_histogram`
  (View > Histogram) refreshes the same panel. GUI smoke confirmed two datasets after open.
* Progress UI: the separate `Gtk.Statusbar` was removed; the bottom `Gtk.ProgressBar` is the
  whole strip with CSS forcing an 18px minimum height and green fill. `_status()` writes
  the status text into the bar.
* Translations expanded for submenus and dialog titles via `_dialog_header()`. Options >
  Language was removed; Options > Frontend Settings now owns language, theme and font size,
  while Backend Settings keeps connector toggles, offline mode and thread limits.
* Custom resize is now a `Gtk.Window` with a `HeaderBar` and `make_draggable()`, verified by
  a unit test that simulates a header drag. Three further audit items are complete: shared
  `job_id` sanitization in `ScratchManager`, UUID fallback in `unique_export_path()`, and
  closing `Gio.DataInputStream` objects when a job finishes.
* Version bumped to `0.2.10` with a `CHANGELOG.md` entry.

---

## 28. v0.2.11 — Throttled Stretch and Backend Dialog Fix

* `HistogramWidget` debounces handle movement: a 1s `GLib.timeout_add` fires once after the
  last movement, applying the low/high cut points if they changed since the last request;
  release still applies immediately. This avoids saturating the CLI while giving live feedback.
* Backend detail dialog bug fixed: `Gtk.Entry` has no `set_selectable()`, so the window
  aborted before `show_all()`. A GUI smoke now confirms the single "ExifTool details"
  window opens after one click and the apt query is logged in the Terminal Drawer.
* Bottom strip CSS now sets `font-size: 13px`, zero border/radius, dark trough and full-height
  green fill; the status text and progress share the same widget.
* Roadmap format audit extended from current research: Astro-TIFF (FITS header in TIFF tag
  270), `.f32raw/.f64raw`, OpenEXR/PFM/RGBE, Bayer dumps, extended camera RAW suffixes,
  planetary MP4/MOV and WebP/JXL/JPEG2000.
* Version bumped to `0.2.11` with a `CHANGELOG.md` entry.

---

## 29. v0.2.12 — Canon CR2 Input via SkyStacker

* SkyStacker docs confirm native pure-Go CR2 decoding and accepted inputs `jpg, jpeg, png,
  cr2, cr3, fits, fit, ser, pgm, ppm, xisf`. Direct CLI verification on a real 10MP CR2
  produced `TIFF/stacked_sum.tif` (3944x2622, 32-bit float RGB) with
  `--tiff --no-postprocess --no-register --overwrite`.
* `ImageWorkspace.prepare()` now special-cases `.cr2`: copies the original into a scratch
  input directory, runs `SkyStackerAdapter.build_raw_import_argv()`, copies the produced
  float TIFF into `working.tiff` and regenerates the PNG preview with ImageMagick. The
  original file is never modified. `MainWindow._open_file()` requires SkyStacker for CR2.
* CR2 remains a high-depth source, so `display_stretch=True` applies to its preview.
  Unit tests cover the argv shape and the full prepare path with a simulated raw engine.
* Version bumped to `0.2.12` with a `CHANGELOG.md` entry; roadmap marks CR2 supported.

---

## 30. v0.2.13 — Settings Depth, Shortcuts and Drag-and-Drop

* Settings gained `binary_overrides`, `scratch_dir`, `cache_dir` and `shortcuts`.
  `BackendRegistry._resolve_binary()` honours a per-connector override, `ScratchManager`
  accepts a root override, and SkyStacker receives `--gaia-cache-dir` from settings.
* `app.DEFAULT_SHORTCUTS` defines accelerators for open/export/metadata/histogram/undo/
  redo/quit/fit; Frontend Settings edits them and `app.apply_shortcuts()` applies them
  immediately. Backend Settings edits binary paths, scratch root and Gaia cache.
* The preview canvas is a `Gtk.Drag` destination for `text/uri-list`; dropped files and
  folders are filtered by `IMAGE_EXTENSIONS` and opened through `_open_file()`.
* Roadmap low-difficulty items 1–3 are complete. Version bumped to `0.2.13`.

---

## 31. v0.2.14 — Japanese UI and Current Refresh State

* Japanese (`ja`) was added to `TRANSLATIONS` and the language selector with menu, dialog,
  panel and status translations. GUI smoke confirmed
  `ファイル / 編集 / 処理 / 天体測定` and Japanese status text.
* Dock panel titles are translated in `_panel_with_close()`, dialog titles in
  `_dialog_header()`, and the main status strings now call `translator.tr()` before being
  written into the bottom progress strip.
* Canonical current state for the opencode right panel: version **0.2.14**, branch `main`,
  latest commit prefix to be confirmed after this change; all execution-queue items 1–10
  are complete; low-difficulty roadmap items 1–3 are complete; 70 unit/integration tests
  pass with 1 opt-in benchmark skipped.

*Note:* the opencode right column is driven by this context file. Updating it here is the
only way I can "refresh" what it displays; there is no opencode CLI command in the docs
to force a UI redraw.

---

## 32. v0.2.15 — Native Blind Solve, More Languages and Recent Files

* SkyStacker docs were re-read (updated 2026-11-19). New section 4 documents
  `--plate-solver native` with a Gaia quad index: `--blind-catalog mag07`, scale bands
  wide/medium/narrow and offline all-sky coverage. `SkyStackerAdapter.build_blind_solve_argv()`
  emits `--image-op plate-solve --plate-solver native --blind-catalog ...` wrapped with
  `/usr/bin/env SKYSTACKER_CATALOGS=<dir>`; `discover_catalog_dir()` finds the manifest.
  A direct solve of `IMG_4062.JPG` still failed matching on that processed JPEG, but the
  CLI path and error reporting are correct.
* Languages: Russian (`ru`) and Chinese (`zh`) added; all menu, submenu, panel, dialog and
  status keys completed for ES/DE/JA/RU/ZH (verified by a key-completeness script).
* File > Open Recent exposes the 10 most recently opened images from persisted settings.
  Drag-and-drop now reads `SelectionData.get_uris()` and accepts drag-motion.
* CPU/RAM meters follow the supplied reference: circular gauge, 60-sample sparkline and
  per-core bars, red at >=75% and green below.
* Version bumped to `0.2.15` with a `CHANGELOG.md` entry.

---

## 33. v0.2.16 — Resizable Window, Selection and Live Relabelling

* `set_resizable(True)` makes the main window resizable/maximizable; GUI smoke confirms it.
* Toolbar Select Area button toggles a drag-to-select overlay on the preview. The pure
  `selection_rectangle()` helper normalises reversed drags and is unit-tested; a GUI smoke
  produced `(20,20,80,60)` for a simulated drag.
* Meter widget height halved to 60px, keeping circular gauge, 60-sample sparkline and
  per-core bars.
* Panel titles and toolbar labels are stored and relabelled when Frontend Settings changes
  the language; a smoke confirmed `Terminal Drawer` becomes `ターミナル` in Japanese.
* Added integration-oriented tests: i18n key completeness across all five languages,
  recent-file action registration and selection rectangle maths.
* Version bumped to `0.2.16` with a `CHANGELOG.md` entry.

---

## 34. v0.2.17 — Accent, Pipeline Export and Transform Cache

* Frontend Settings now offers an accent colour; `MainWindow._apply_progress_css()`
  regenerates the GTK CSS provider with the chosen colour and removes the previous one.
* `core/pipeline_export.py` converts `cli_start` operation-log entries into a reproducible
  shell script or Makefile using `shlex.quote`. Available from File > Export Pipeline and
  from `scripts/export_pipeline.py`.
* `ImageWorkspace` caches transform results by SHA-256 of the input TIFF bytes plus the
  serialized argv; identical jobs reuse the cached TIFF and skip the external CLI while
  still regenerating the preview. Cache root comes from `settings.cache_dir` or XDG cache.
* Roadmap low-difficulty items 4–6 complete; new tests cover pipeline quoting and the
  content-hash cache.
* Version bumped to `0.2.17` with a `CHANGELOG.md` entry.

---

## 35. v0.2.18 — Threads, Log Rotation and Batch Conversion

* `ImageMagickAdapter.thread_limit` inserts `-limit thread N` into import, preview,
  export, transform and batch argv; it is initialised from `settings.threads` and updated
  in Backend Settings.
* `OperationLog` rotates the JSONL file when it exceeds `max_bytes`, keeping numbered
  backups. `cli_end` already records `input_bytes`/`output_bytes`.
* File > Batch Convert uses `mogrify -format <ext> -path <dir> ...` with file, format and
  destination dialogs; results are logged in the Terminal Drawer.
* Roadmap items 7, 10, 13 and 14 are complete. Tests cover thread serialization, batch
  argv and rotation.
* Version bumped to `0.2.18` with a `CHANGELOG.md` entry.
---

## 36. v0.2.19 — Error Details, Documentation and Robustness Tests

* Error dialogs are now draggable `Gtk.Window`s with a short summary and a collapsible
  `Gtk.Expander` containing the full backend `stderr`.
* Added a Mermaid architecture diagram to `README.md`, adapter contract docstrings to
  `adapters/base.py` and `adapters/magick.py`, and the checklist/limitations below.
* Robustness tests added for corrupt settings, malformed histogram lines, Unicode export
  names, process cancellation and per-image undo isolation. Two real bugs were fixed:
  shallow-copied `DEFAULTS` leaked mutable state between `SettingsManager` instances, and
  malformed histogram components raised `ValueError`.
* Version bumped to `0.2.19`.

### Adding an adapter — checklist

1. Add a `BackendSpec` (binary, candidate alternatives, version args) in `core/backends.py`.
2. Register the action in `ACTION_BACKENDS` and, when implemented, `IMPLEMENTED_ACTIONS`.
3. Implement a `CliAdapter` subclass with `build_*_argv()` returning argv lists only.
4. Add the menu/toolbar entry in `MENU_LAYOUT` and its translation keys in `core/i18n.py`.
5. Add unit tests for argv serialization, ENOENT/nonzero exit and scratch cleanup.
6. Register new image extensions in `IMAGE_EXTENSIONS`, `packaging/astro-studio.desktop`
   and, for non-standard suffixes, `packaging/astro-studio-mime.xml`.

### Known limitations

- SkyStacker now reads TIFF via goTiff; ImageMagick still produces the TIFF-to-PNG previews.
- RGB FITS may be stored as three HDUs; import uses `-combine`, unusual multi-extension
  files may need manual handling.
- Display stretch (`-evaluate`, `-level`) affects only the PNG preview; scientific exports
  stay linear.
- Native blind plate solving needs a Gaia quad catalog; `mag07` covers wide fields only.

---

## 37. v0.2.20 — Job Manager, Frame Table and Calibration Discovery

* `ProcessEngine` now emits `on_job_start`/`on_job_end` callbacks; `JobManager` stores
  job id, argv, state, duration and exit code. The right dock shows a Jobs panel with a
  Retry button that replays the original argv.
* View > Frame Table opens a dialog whose Measure button runs SkyStacker
  `--image-op measure-quality` per open image and parses `image_measurements.json`
  into columns File/Size/Stars/HFR/SNR/Quality.
* Processing > Detect Calibration Folders scans a session root case-insensitively for
  Bias/Biases, Dark/Darks, Flat/Flats and Light/Lights, excluding non-image files, and
  reports counts in the log and an info dialog.
* Roadmap medium-difficulty items 1–3 are complete. Version bumped to `0.2.20`.

---

## 38. v0.2.21 — Siril, BPM and WCS Sidecars

* `adapters/siril.py` generates Siril `.ssf` scripts for calibration and stacking and
  invokes `siril-cli -s <script>`; actions are disabled because `siril-cli` is not
  installed here, so no results are fabricated.
* `core/bpm.py` validates bad-pixel-map density against the 0.1% cap; SkyStacker
  `--bpm-auto --bpm-auto-sigma` is exposed as a Processing action.
* `core/wcs.py` converts SkyStacker's radian WCS/0-based CRPIX to FITS header values and
  writes a `.wcs.json` sidecar next to exported FITS files. Installed tools (ExifTool)
  cannot write arbitrary FITS keywords, so direct header rewriting is not attempted.
* Roadmap medium-difficulty items 4–6 complete. Version bumped to `0.2.21`.

---

## 39. v0.2.22 — Alternative Solvers, Gaia Cache and Sessions

* `adapters/astrometry.py` builds direct `solve-field` and `astap` argv with RA/Dec
  seeds, ±20% scale hints derived from focal length/pixel size, and logs a warning when
  no pointing seed is supplied. Both binaries are absent here, so actions gated on them
  stay disabled.
* Gaia cache management adds `gaia_nside` (default 64) to settings, passes
  `--gaia-nside/--gaia-cache-dir/--gaia-offline` to SkyStacker, and offers a cache info
  dialog with tile count and effective flags.
* Session save/resume persists open images, per-image stretch points, plate solutions
  and recent files; resuming reopens images and reapplies display stretches.
* Roadmap medium-difficulty items 7–9 are complete. Version bumped to `0.2.22`.

---

## 40. v0.2.23 — Multi-document Strip, WCS Overlay and Optional Tools

* A thumbnail strip below the canvas lists open images and switches the active preview;
  View > Before / After runs ImageMagick `-compose difference -composite -auto-level`
  against the first stored TIFF snapshot and displays the result in a movable window.
* View > WCS Overlay draws a crosshair and circle at the plate solution's 0-based CRPIX
  reference pixel. `overlay_center()` uses CRPIX directly; FITS sidecars add 1 for the
  1-based FITS convention.
* `ExternalToolAdapter` supplies argv for RawTherapee/Darktable/LibRaw, Hugin, enfuse and
  GIMP. Menu entries are gated by backend availability; none of these binaries are
  installed here, so no results are fabricated.
* Roadmap medium-difficulty items 10–12 are complete. Version bumped to `0.2.23`.

---

## 41. v0.2.24 — Presets, Annotations and Linear Guard

* `core/presets.py` parses ExifTool key/value text and suggests denoise/sharpen/stacking
  actions from ISO, exposure and optional frame diagnostics; exposed as
  Processing > Suggest Presets.
* `core/annotations.py` stores label/arrow/circle markup and builds ImageMagick `-draw`
  argv to burn it into a preview PNG only; original TIFFs are untouched.
* `core/linear_guard.py` rejects background/deconvolution/starless operations after a
  non-linear stretch unless `settings.linear_override` is enabled.
* Roadmap medium-difficulty items 13–15 are complete. Version bumped to `0.2.24`.

---

## 42. v0.2.25 — Provenance, Histogram Gamma and FITS Compression

* `core/provenance.py` builds a derivation tree from the original path, recorded CLI
  operations and the preview PNG; View > Derivation Tree displays it in a dialog.
* Histogram panel gains a shadow loupe (0–0.05 intensities) and a gamma slider that is
  serialized as ImageMagick `-evaluate Pow <gamma>` for the preview PNG only.
* `adapters/fits_compression.py` provides fpack argv for RICE_1/GZIP_1/GZIP_2/
  HCOMPRESS_1/PLIO_1 plus gzip `-kf` for whole-file `.gz`; backend gating disables the
  action when neither binary exists.
* Roadmap medium-difficulty items 16–18 are complete (17 partially: click-to-anchor and
  staged GHS remain planned). Version bumped to `0.2.25`.

---

## 43. v0.2.26 — RAW, SER and AVI Support

* `core/raw_formats.py` reads ExifTool metadata and warns about lossy RAW compression,
  Bayer CFA patterns and linear DNGs, exposed via File > Inspect RAW/DNG.
* `core/video.py` parses the SER header (dimensions, bit depth, frame count, Bayer
  pattern) and builds ffmpeg argv to extract frames to scratch; exposed via File > Inspect SER.
* AVI codecs are probed with `ffprobe` and validated against a lossless whitelist;
  MJPEG/DIVX/XVID/H264 are rejected before stretching, with a clear info dialog.
* Roadmap medium-difficulty items 19–21 are complete. Version bumped to `0.2.26`.

---

## 44. v0.2.27 — Startup Crash Fix

* The application failed to open its window because `_build_layout()` passed an undefined
  `app` variable to `JobPanel`; changed to `self.app.job_manager`. A stale process held
  the GTK application id, making later launches exit silently.
* Added `tests/test_ui_startup.py` (skipped without DISPLAY) that constructs `MainWindow`
  and asserts the Backends, Histogram and Jobs panels exist, preventing regressions.
* Version bumped to `0.2.27`.

---

## 45. v0.2.28 — Meter Cleanup, Resize Control and Catalog Env

* Resource meters now draw only a circular gauge with the percentage centered inside
  plus a thin linear bar and optional per-core bars; the time-series sparkline was
  removed and height reduced to 56px.
* Added a Maximize/Restore toolbar action and lowered the preview minimum size to
  320x240 so the main window can actually be resized even without WM decorations.
* SkyStacker plate solve, sky map and survey cutout now wrap argv with
  `SKYSTACKER_CATALOGS=<dir>` and pass `--blind-catalog mag07` for non-native solvers
  whenever the catalog directory is discovered.
* Direct CLI verification on the M42 JPEG still fails: no `solve-field`, no ASTAP, no
  API key, and the native quad index finds 20 votes but no consistent transform. This
  is a SkyStacker/backend limitation, not an AstroStudio argv bug.
* Version bumped to `0.2.28`.

---

## 46. v0.2.29 — Visible Version and Actionable Solver Errors

* Runtime inspection confirmed v0.2.28 was actually running: meter allocation 347x56,
  toolbar includes `Maximize`, and the rendered meter shows the percentage inside the
  circle with a thin linear bar. GUI changes were present; the user's session had not
  picked them up because the window was opened before the update.
* The status bar now starts with `Astro Studio vX.Y.Z ready` so the running version is
  visible without opening About.
* Plate-solve failures now produce actionable hints inside the expandable error dialog:
  install astrometry.net indexes or ASTAP, set `AN_API_KEY`, or use a linear frame with
  a precise RA/Dec seed when Gaia matching finds no consistent transform.
* Version bumped to `0.2.29`.

---

## 47. v0.2.30 — 16-bit Histogram Fix

* Screenshot inspection confirmed the new meters and maximize control were present; the
  real remaining bug was the histogram: the working TIFF showed a single bin because
  16-bit RGB components (e.g. 1185/2164/2516) were clamped to 255 by the parser.
* `histogram_argv()` now adds `-depth 8` and `parse_histogram_text()` scales any
  component above 255 by /257. A GUI smoke now reports 61 bins for both the PNG and the
  TIFF instead of 1.
* `screenshots/` added to `.gitignore`. Version bumped to `0.2.30`.

---

## 48. v0.2.31 — Window Geometry Root Cause and Hardening

* Detailed analysis with `wmctrl`/`xprop` showed `WM_NORMAL_HINTS` minimum size
  **484x868** while the X screen is **1366x768**. GNOME refused to maximize/resize
  because the minimum height exceeded the available height. The right dock stacked
  fixed-minimum panels (backends, metadata, histogram, jobs, terminal).
* Fix: right dock is now a `Gtk.ScrolledWindow` (`right_scroll`) with reduced child
  minimum heights; measured minimum is now **484x258** and `wmctrl` maximization sets
  `_NET_WM_STATE_MAXIMIZED_VERT/HORZ` correctly (window 1366x704).
* Hardening: `MainWindow.validate_geometry()` logs minimum vs screen size at startup and
  hides optional panels if a future change recreates an oversized minimum. Added unit
  tests for the helper/preferred size and an opt-in X11 integration test
  (`ASTROSTUDIO_WM_TEST=1`) that launches the app in a private D-Bus session and verifies
  min size and maximization.
* Version bumped to `0.2.31`.

---

## 49. v0.2.32 — Gamma, Thumbnails and Fullscreen UX

* Gamma changes are debounced with an 800ms timer and log the applied low/high/gamma
  values; the CLI preview command was verified (`-evaluate Pow 2.000`).
* Thumbnail strip now switches images on single click (`selection-changed`), is cleared by
  Close/Close All, and is hidden by default via `show_thumbnails`. CPU/RAM panel has a
  matching `show_resources` toggle. Both are applied **after** `show_all()` in
  `do_activate()` so GTK does not override visibility.
* The toolbar Maximize button was ineffective because `toggle-maximize` was never added to
  `app.ACTION_NAMES`. Replaced by a registered `fullscreen` action; ESC exits fullscreen,
  and right-click on the canvas opens a popup with a `menu` entry that shows the same
  `Gio.Menu` model as the application menu bar.
* Open Recent is inserted immediately after Open in the File menu.
* RAM meter keeps only the circular gauge; CPU keeps gauge, linear bar and per-core bars.
* Version bumped to `0.2.32`.

---

## 50. v0.2.33 — Panels, Fullscreen and Context Menu Fixes

* CPU/RAM indicator group is now a closable dock panel with a horizontal layout: CPU
  gauge/bars first, RAM circle to its right. RAM linear bar was removed earlier.
* Fullscreen mode hides menu bar, toolbar, all dock panels and status bar. A transient
  progress/status bar is shown at job start and hidden again 1 second after job end.
* Right-click popups are retained on `self` until `deactivate`, fixing the intermittent
  "third click works" behaviour. The popup now uses `_build_menu_model()`, the same model
  as the menu bar, so Open Recent appears. A second `Crop Selection` item is sensitive
  only when right-clicking inside a previously drawn selection; it delegates a `-crop`
  transform to the external CLI through `ImageWorkspace`.
* Derivation Tree was broken by another `Gtk.ScrolledWindow.set_min_content_size()`
  call; replaced with width/height setters and covered by a UI test.
* Version bumped to `0.2.33`.

---

## 51. v0.2.34 — Fullscreen Canvas, Panels and Rotation

* Fullscreen hides the preview frame label and the right dock container in addition to
  all chrome; measured canvas allocation is 1366x744 on a 1366x768 screen.
* Right-click menus call `popup_at_pointer(None)` and keep widget references until
  replaced, avoiding the intermittent "third click works" behaviour. The app menu comes
  from the same model as the menu bar (Open Recent included). Crop Selection clears the
  selection rectangle once the external `-crop` transform completes.
* Resource meters are asymmetric: CPU 200px with linear/per-core bars, RAM 84px circle
  only. Title and percentage are drawn inside each circle.
* View > Panels groups toggles for Backends, Histogram, Terminal, Resources and Jobs.
* Processing > Rotate Image offers 90 CW/CCW, a free angle dialog and rotation by a
  mouse-drawn segment (angle from `atan2(dy, dx)` serialized as `-rotate <degrees>`).
* Version bumped to `0.2.34`.

---

## 52. v0.2.35 — Rotation Mode, Toolbar State and Meter Width

* Rotation-by-segment was alternating with area selection because the two modes were not
  mutually exclusive and rotation mode was never cleared after finishing. Now enabling
  rotation disables selection, and a finished segment resets rotation mode; the next
  toolbar press starts a new rotation instead of drawing a rectangle.
* Undo/Redo toolbar buttons follow `Gio.SimpleAction` sensitivity: disabled buttons are
  insensitive and styled with `.inactive-action` (greyed) at the end of the history chain.
* CPU/RAM dock uses dynamic widths: CPU meter has `hexpand=True` and grows with the panel
  (259px measured), RAM stays fixed at 84px around its circle.
* Fullscreen canvas now measures the complete 1366x768 screen.
* Version bumped to `0.2.35`.

---

## 53. v0.2.36 — Rotation Failure and Before/After Canvas

* Log analysis showed `convert -rotate 55.7496 ...` exiting 1 with
  "TIFF: negative image positions unsupported". ImageMagick rotation creates canvas
  offsets that IM6 cannot store in TIFF; `-rotate <angle> +repage` fixes it. Verified with
  a real CLI integration test producing a rotated TIFF.
* Rotate-by-segment is now idempotent (always enables the mode) and calls `popdown()` on
  open context/app menus before activating, which fixes the first-attempt failure in
  fullscreen where a lingering popup swallowed the first left-click.
* Before / After now opens the generated difference map through `_open_file()` so it is
  a new image in the canvas/workspace instead of a separate viewer window.
* Version bumped to `0.2.36`.


---

## 54. v0.2.37 — Star/Diffuse Layers, Reliable Popups and Display Exports

* SkyStacker 0.6.1 exposes `--export-stars FILE` and `--classify-objects FILE` as
  report-only jobs used with `--process-image` and no `--image-op`. Adapters build argv
  arrays for both; reports are parsed in `core/star_catalog.py` and
  `core/object_classification.py`. Real CLI runs on `assets/MilkyWay.jpg` and a synthetic
  field produced 500 stars and 177 diffuse components respectively.
* Astrometry > Export Star Catalog and Astrometry > Classify Objects run the CLI
  asynchronously, render numbered overlays in the preview, and write SVG sidecars
  (`star_layer.svg`, `object_layer.svg`) in the job scratch directory. Pipeline pixels
  are never modified; scientific exports remain linear.
* Right-click is now a manually built GTK menu with nested submenus, a Crop Selection
  item tied to the current selection, and recent transforms from settings after a
  separator. Running a popup item dismisses popups first and dispatches directly to the
  window handler, so the real app no longer relies on GApplication registration in the
  test harness and the first click after rotation works.
* `Ctrl+Z` and `Ctrl+Y` are registered accelerators with settings migration; closing an
  image loads the previous one from the workspace history when available. Low-depth
  display formats (JPEG/PNG/BMP) get gamma/level flags in the CLI export argv, while
  FITS/TIFF scientific exports stay linear.
* Tests cover argv building, report parsing, SVG layers, real CLI reports, popup dispatch,
  recent transforms and close-to-previous-image. Full suite: 163 passed, 2 skipped.
* Version bumped to `0.2.37`.


---

## 55. v0.2.38 — Segment Rotation and Star Overlay Rendering

* A stray `button-release-event` delivered while the popup menu closed was interpreted as
  the end of a rotate-by-segment gesture, disabling rotation mode before the real drag.
  `_on_canvas_release()` now ignores releases when no segment has been started, so the
  first drag draws the segment as intended.
* Debugged the M42 star overlay with the persistent operation log: the CLI produced a
  76,755-byte catalog with 500 detections. Only one circle was visible because
  `PreviewPane._on_draw()` called `cr.fill_text()`, which does not exist in pycairo 1.16,
  aborting the draw loop after the first star. Replaced with `cr.show_text()`; up to 500
  detections are rendered, with rank labels on the 30 brightest.
* `set_pixbuf()` clears star/object layers when loading another image, preventing stale
  overlays. The terminal log now records detection count, preview size and top flux.
* Version bumped to `0.2.38`.


---

## 56. v0.2.39 — Segment Hint, Overlay Tooltips and Recent Actions

* Rotate-by-segment activation records a short guard interval so events generated while
  the popup closes cannot consume the first drag; rotation mode is also checked before
  double-click zoom. A translated `Draw a segment` tooltip follows the pointer and the
  canvas uses a crosshair cursor until the segment is finished.
* `PreviewPane._layer_hit()` finds star/diffuse overlays under the pointer and displays
  a tooltip with rank, coordinates, flux, size, HFR, eccentricity or object type, area,
  ellipticity and CAS/Gini/M20 morphology. The small strokes seen in the overlay are the
  numeric rank labels, not leader lines.
* Recent transforms are deduplicated by label + params + relaunch target. Segment and
  free-angle rotations store a `relaunch` target so selecting them from the right-click
  history reopens the interaction instead of silently reusing the previous angle.
* Version bumped to `0.2.39`.


---

## 57. v0.2.40 — Segment Completion and Open Recent Regression

* Real X11 reproduction exposed the real rotate-by-segment failure: on release,
  `PreviewPane.set_rotation_mode(False)` raised `AttributeError` because
  `Gdk.CursorType.DEFAULT` does not exist in this GDK build. The exception happened before
  `_rotate_image()`, so no CLI job was launched. Cursor reset now uses `LEFT_PTR`, and the
  applied angle is logged and shown in the status bar. A real drag of -11.31 degrees was
  verified end to end in the operation log.
* The manual right-click popup had replaced the model-based menu and lost the dynamically
  inserted `Open Recent` submenu. `_entries_with_recent()` now injects the same recent
  paths (or the "No recent images" fallback) into the File submenu of the popup.
* Regression coverage: Open Recent present/absent cases, cursor restoration on a realized
  widget, segment release dispatching `(angle, label, relaunch)` and a real-CLI workspace
  rotation whose preview PNG bytes and dimensions change.
* Version bumped to `0.2.40`.


---

## 58. v0.3.0 — Roadmap Items 23-25 and Layer Toggles

* First `MainWindow` refactor: menu construction moved to `ui/menu_builder.py`, action
  dispatch to `ui/action_registry.py`, dock visibility to `ui/dock_manager.py` and dialog
  headers to `ui/dialogs.py`. `MainWindow` delegates to these collaborators; all previous
  methods and behaviour are preserved.
* Added View > Layers toggles for the star-identification and diffuse-object overlays;
  visibility is owned by `PreviewPane` and reported in the status bar.
* A quick click without a drawn segment no longer silently ends rotation mode: the mode
  stays armed and the status bar explains that no segment was drawn.
* Quality tooling: `mypy.ini` (strict, core/adapters), `requirements-dev.txt`,
  `.pre-commit-config.yaml` and `.github/workflows/ci.yml` with a 70% coverage gate and
  `desktop-file-validate`. Added `tests/test_ui_smoke.py` for window, menu, dock and
  metadata/histogram coverage. Local environment lacks the optional dev tools, so they
  are pinned for CI.
* Roadmap items 23-25 are now checked; version bumped to `0.3.0`.


---

## 59. v0.3.1 — SkyStacker Filter Menu

* Added `core/sky_filters.py` with 24 single-image SkyStacker presets grouped under
  Filter > SkyStacker Blur & Sharpen / Background / Stretch / Denoise / Deconvolution /
  Starless. Every new action is gated on the SkyStacker backend and translated in all
  supported UI languages.
* SkyStacker now decodes TIFF through its first-party goTiff module, so
  `ImageWorkspace.transform_via_image_op()` passes the 16-bit working TIFF directly.
  The image-op JPEG product is converted back to a 16-bit TIFF by ImageMagick before the
  normal preview regeneration. Undo/redo snapshots are preserved.
* Background, deconvolution and starless presets still pass through the linear guard.
  Real-CLI integration verifies that the working TIFF and preview PNG both change.
* Version bumped to `0.3.1`.


---

## 60. v0.3.2 — Flux-scaled Stars and Highlightable Overlays

* `star_display_radius()` maps flux logarithmically to circle radius (3-10 px); the live
  overlay, hit-testing and `star_layer.svg` all use the same value, so brighter stars are
  visibly larger.
* Rank labels now have explicit leader lines. Those straight strokes are label leaders,
  not detected invariant patterns: SkyStacker's `stars[]` only carries `x_px`, `y_px`,
  `flux`, `size_px`, `eccentricity` and `hfr_px`. Hovering a leader states this explicitly.
* `PreviewPane.hover_target` tracks the hovered star, leader or diffuse object and redraws
  only that item with a brighter, thicker outline. Leaving the canvas clears the target.
* Version bumped to `0.3.2`.


---

## 61. v0.3.3 — Rank Labels Without Leaders

* Removed the SVG leader lines and the canvas leader strokes. Every rendered star keeps
  its rank number directly beside its flux-scaled circle, in both the live overlay and
  `star_layer.svg`.
* `PreviewPane` hit-testing includes the small label box, so hovering the number selects
  the same star as hovering the circle; the highlighted state now also enlarges and
  brightens the label.
* Version bumped to `0.3.3`.


---

## 62. v0.3.4 — Cairo Path Fix for Star Overlay Lines

* The long yellow lines were not leader strokes: `cairo_show_text()` left a current point
  and the next `cairo_arc()` connected it to the following star, forming a graph across
  the whole canvas. `cr.new_path()` is now called after each rank label and before each
  circle, so every arc is an isolated subpath.
* Reproduced with a fresh GTK process (`Rosetta.jpg` + Export Star Catalog): the overlay
  now contains only flux-scaled circles and their rank numbers.
* The confusing screenshot came from a stale Astro Studio process; single-instance
  forwarding kept the old Python module loaded. Always restart the app after code changes.
* Version bumped to `0.3.4`.


---

## 63. v0.3.5 — Native TIFF Image Ops and Catalog-Hint Roadmap

* Verified in SkyStacker 0.6.1 docs and CLI that goTiff decodes 8/16-bit and float TIFF,
  classic and BigTIFF, including Astro-TIFF tag 270. A real `--process-image ...tiff
  --image-op blur` run succeeded, so the old "cannot decode TIFF" limitation was removed
  from `AGENTS.md` and the project context.
* `ImageWorkspace.transform_via_image_op()` now sends the working TIFF directly to
  SkyStacker; only the returned JPEG product still needs an ImageMagick conversion back
  to 16-bit TIFF. Unit and real-CLI tests cover the new argv path.
* Added high-difficulty roadmap item 11: derive plate-solving seeds from catalog
  references in filenames (`M42`, `NGC 1976`, `IC 434`, `Cxx`, common names) using a
  bundled offline OpenNGC dataset (CC BY-SA 4.0, with attribution and license shipped),
  with ambiguity handling and no fabricated coordinates. SIMBAD/CDS-derived additions
  are ODbL 1.0 and must stay separately attributed.
* Version bumped to `0.3.5`.


---

## 64. v0.3.6 — Filename Catalog Hints (Roadmap 11)

* Added `core/catalog_hints.py` and a compact bundled OpenNGC projection at
  `data/openngc_hints.json` (13,643 entries: J2000 RA/Dec, Messier/NGC/IC/Caldwell
  aliases and common names). `data/CREDITS.md` and
  `data/LICENSES/OpenNGC-CC-BY-SA-4.0.txt` ship the required attribution and license.
* `MainWindow._filename_hint()` parses the active image basename, resolves unambiguous
  matches and prefills RA/Dec in the Plate Solving dialog; the existing
  `--plate-center RA,DEC` argv path is reused. Multiple different objects in a filename
  are reported in the terminal and no seed is guessed.
* Verified `Orion-M42-Riofrio-2026-11-09.png` resolves to M42 at 83.818667,-5.389667 and
  `Orion-Nebula`/`NGC1976` resolve to the same coordinates.
* Version bumped to `0.3.6`.
