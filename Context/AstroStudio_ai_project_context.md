# Astro Studio — AI Project Context & Engineering Baseline

## 1. Project Identity & Core Mandate

* **Application Name:** Astro Studio
* **Platform & Toolkit:** Native Linux / Ubuntu desktop application built with **GTK 3.24** (GNOME standard) and GLib, implemented in **Python 3.8 with PyGObject** (`Gio.Subprocess` for async CLI execution). GTK4 is not available in the development environment.
* **Version:** `v0.1.0` (Initial architectural baseline)
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
   * **Parameter Inspector & Terminal Drawer:** Dynamic UI controls mapped to backend CLI flags, alongside a real-time log drawer streaming `stdout`/`stderr` from active child processes.

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
   * Results (installed / not installed / version / error) populate the GUI "Backends" panel and the log drawer, and drive `Gio.SimpleAction` sensitivity: a menu item is enabled only if its adapter is implemented and at least one required backend is installed. Actions whose backend is missing stay visible but disabled.
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
* **Modules created:** `astrostudio/app.py` (application, actions, discovery scheduling), `astrostudio/core/` (`command_builder.py`, `process_engine.py`, `scratch.py`, `backends.py`), `astrostudio/adapters/` (`base.py`, `magick.py`, `exiftool.py`), `astrostudio/ui/` (`main_window.py`, `preview.py`).
* **Backend availability at development time:** `exiftool` 11.88 and GIMP 2.10.18 detected at startup; `magick` and the astronomical CLIs (Siril, ASTAP, etc.) are absent, so their actions are disabled rather than crashing or falling back to in-process processing. `AGENTS.md` at the project root records these standing rules.
* **Desktop integration:** `packaging/` holds the SVG icon, the `.desktop` template, the launcher script and a user-level `install.sh` that installs into `$XDG_DATA_HOME` (`~/.local/share`), refreshes caches and enables launching Astro Studio from the application menu (`gtk-launch astro-studio`). The desktop file was validated with `desktop-file-validate`.
* **User documentation:** `README.md` at the project root documents requirements, how to run the app, the automated test commands and the manual verification steps (including the ImageMagick export prerequisite).
* **Version control and planning:** the project is a Git repository; `roadmap.md` tracks milestones v0.1.0 through v1.0.0 with status tags matching the GUI specification. Commit each logical change, keep this context file and the roadmap updated in the same change, and never push or rewrite history without explicit user request.
* **Verification:** `python3 -m compileall -q astrostudio tests` and `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/` (15 tests passing; pytest autoload is broken by an unrelated Dash plugin in this environment).