# Astro Studio — GUI Specification (CLI-Orchestration Contract)

This document specifies the graphical interface of Astro Studio. Astro Studio is a **zero-processing front-end**: no widget in this interface calibrates, stacks, stretches, filters, or otherwise transforms pixel data. Every menu item and toolbar button implements the same orchestration contract:

1. Collect input paths and parameters in GTK widgets.
2. Serialize them into a sanitized `argv` vector through the matching CLI adapter (never a shell string).
3. Spawn the external binary asynchronously with `Gio.Subprocess`; stream `stdout`/`stderr` into the terminal drawer.
4. Read the artifact written by the backend into the session scratch directory, render it **read-only** on the canvas (e.g. `GdkPixbuf`), and/or copy it to the user-chosen export path.
5. Clean up scratch artifacts on session close unless preserved for resume.

"Action" in this document therefore means *the GUI prepares, launches, monitors, and displays the result of an external CLI job*. The algorithm always lives in a third-party binary; the GUI owns state, rendering, IPC, and file routing only.

## 1. Top-Level Layout & Main Window Architecture

* **Main Frame (`Gtk.ApplicationWindow`):** Hosts the global menu bar, toolbars, status bar, dockable workspace container, and the collapsible terminal drawer. Follows GNOME HIG.
* **Child Image Canvas Panes:** Multi-document/single-document view supporting multiple loaded files, zoom from fit-to-window to custom magnification, and read-only pixel inspection. The canvas never modifies the buffer it displays; a transformed image is a *new file* produced by a backend and reloaded into view.
* **Parameter Inspector:** Dynamic panels whose controls map one-to-one to flags of the selected CLI adapter. Widget defaults and tooltips must equal the defaults serialized by the Command Builder.
* **Terminal Drawer:** Line-buffered `stdout`/`stderr` view of active child processes, with cancel (`SIGTERM`, then `SIGKILL`) and exit-code display.
* **Status Bar:** Cursor coordinates (X, Y), intensity value read from the rendered preview (display only), zoom percentage, active backend, and job status.

## 2. Universal Action Flow (applies to every item below)

```
Input paths + GUI parameters
        -> Adapter.build_argv()            (argv list, no shell)
        -> ProcessEngine.run_async()       (Gio.Subprocess, GMainContext)
        -> <scratch>/<job>/output.<ext>    (backend writes the file)
        -> Canvas.render(path)             (read-only display)
        -> Export path or scratch cleanup
```

* **Scratch location:** `<XDG_RUNTIME_DIR>/astro-studio/<session>/<job>/`, falling back to `/tmp/astro_studio_<pid>/`. Raw inputs are never written to; all outputs go to scratch or an explicit user export path.
* **Formats:** Scientific linear artifacts (`.fits`, `.xisf`, `.f32raw`, 16/32-bit `.tiff`) are kept distinct in the UI from display-stretched previews (8-bit `.jpg`, `.png`, `.bmp`). Metadata/WCS headers are preserved when the target backend supports it.
* **Startup discovery:** On activation the app checks every connector binary for installation and queries its version asynchronously (`Gio.Subprocess`, e.g. `magick -version`, `exiftool -ver`). Results appear in the "Backends" panel and terminal drawer; menu actions are enabled only when their adapter is implemented and at least one required backend is installed. Missing version output keeps the backend available with version `unknown`.
* **Missing backend:** If a binary is absent (`ENOENT`) or exits non-zero, the action stays disabled/marked unavailable and the error is reported in the terminal drawer; the GUI never falls back to an in-process implementation.

## 3. Menu Bar Structure and Options

Each entry lists the backend that performs the work. Tags: **[P1]** implemented in the initial skeleton, **[P2]** adapter defined / UI pending, **[P3]** planned.

### 3.1 File (`File`)

| Command | GUI responsibility | Backend / CLI action | I/O routing | Status |
| --- | --- | --- | --- | --- |
| Open (`Ctrl+O`) | Choose local files and render them | None (read-only decode for display, `GdkPixbuf`) | Source files stay read-only | [P1] |
| Save As / Export | Choose target format and destination | `magick`, `rawtherapee-cli`, or `darktable-cli` conversion | Input path -> scratch -> user export path | [P1] |
| Close / Close All | Clear open views and job state | None | Scratch kept until session end | [P1] |
| Batch | Select directory, pattern, target format, flags | `gm mogrify` / `magick mogrify` batch argv built by adapter | Directory -> scratch -> export directory | [P2] |
| Exit | Cancel active jobs, clean scratch, quit | None | Scratch removed unless resume requested | [P1] |

### 3.2 Edit (`Edit`)

* **Undo / Redo (`Ctrl+Z` / `Ctrl+Shift+Z`):** Reverts or restores *pipeline configuration and UI state only* (selected files, adapter flags, parameter history). It never reverts image pixels; to undo a transformation the user re-runs the backend from the original input or a preserved intermediate. [P1]
* **Cut / Copy / Paste:** Transfers *file references and job configurations* through the clipboard, not raster buffers. A pasted image is rendered from its file path. [P3]
* **Select Area / Reset Selection:** Defines a crop rectangle that the Command Builder serializes as backend geometry flags (e.g. `magick -crop WxH+X+Y`). The GUI does not crop pixels itself. [P2]
* **Clone Stamp:** No in-app brush. Delegated to headless `gimp -i -b` (Script-Fu/Python-Fu) or a PhotoFlow `.pfp` pipeline; the result is reloaded from scratch. [P3]

### 3.3 Processing (`Processing`)

* **Calibration (Master Dark / Master Flat / Darks / Flats / Biases):** The GUI discovers calibration folders case-insensitively (`Light(s)`, `Dark(s)`, `Flat(s)`, `Bias(es)`) and exposes real-frame selectors; `siril-cli` / `skystacker` build masters via CLI flags. Synthetic bias/dark/flat generation is never exposed. Output masters are written under scratch and registered as new inputs for stacking. [P2]
* **Stacking (Add Images / Multi-point Alignment):** File list and quality metrics (SNR, FWHM/HFR, eccentricity, background sigma, footprint) are collected in the frame table; registration and stacking flags are serialized to `siril-cli` / `skystacker` / `astap_cli`. Affine shear <= 0.10 and anisotropy <= 1.10 guards are enforced by the adapter before spawning. [P2]
* **Image Geometry:** Resize/scale, rotate, flip, and mirror are serialized as backend flags (`magick -resize`, `-rotate`, `-flip`, `-flop`). [P1 for resize/export; P2 for the rest]
* **Field Derotator / Planet Alignment:** Delegated to an external alignment backend; unavailable until an adapter exists. [P3]

### 3.4 Arithmetic (`Arithmetic`)

* **Image Combination (Add / Subtract / Multiply / Divide):** Two input paths plus the operator are mapped to backend expression flags (e.g. `magick ... -evaluate-sequence Add/Subtract/Multiply/Divide`); output is a new scratch file. [P2]
* **Constant Operations:** Scalar operations are serialized as CLI evaluate arguments, never applied to a GUI buffer. [P2]
* **RGB / LRGB Combination:** Channel file paths are passed to the backend's channel-combine flags. [P2]
* **Split Channels:** Delegated to `magick` channel separation into scratch outputs. [P2]

### 3.5 Color (`Color`)

* **Histogram Manipulation:** Black point, white point, and gamma controls set backend stretch flags (e.g. RawTherapee `.pp3`, darktable XMP, Siril STF/MTF). The GUI only displays the resulting file. [P2]
* **Curves Adjustment (RGB / Luminance):** Control points are written into a backend-readable profile (`.pp3`, XMP, `.pfp`) passed as a CLI argument; no in-app spline evaluation. [P3]
* **Color Saturation / Balance:** Serialized as backend flags (e.g. `magick -modulate`, white-balance coefficients in RAW developer profiles). [P2]
* **Background Neutralization / Gradient Removal:** Delegated to Siril/PhotoFlow background-extraction flags. Linear-space operations are chained only before non-linear stretching unless the user explicitly overrides the linear guard. [P2]

### 3.6 Filter (`Filter`)

* **Sharpening:** Unsharp mask and other sharpening are serialized as backend flags (e.g. `magick -unsharp 1.5x1+0.7+0.02`). Deconvolution is delegated to Siril/PhotoFlow. [P1 for unsharp; P2 for deconvolution]
* **Smoothing & Denoising:** Gaussian/median/wavelet denoise delegated to `magick` or RAW developers (`rawtherapee-cli`, `darktable-cli`). [P2]
* **Specialized Astronomical Filters:** Star-size reduction, spike suppression, and morphological filters delegated to Siril/skystacker adapters. [P3]

### 3.7 View (`View`)

* **Zoom Controls (In / Out / Fit / 1:1):** Read-only manipulation of the preview widget; no image data is changed. [P1]
* **Histogram Display:** The backend is asked to emit histogram data (e.g. ImageMagick `histogram:` text) into scratch; the GUI parses that text and draws the chart. It does not compute pixel statistics internally. [P2]
* **Pixel Line Profile (`Pixellinie als Diagramm`):** A drawn line becomes a crop/coordinate request to the backend (e.g. `magick ... txt:`); the returned values are plotted by the GUI. [P3]
* **FITS Header Inspector:** `exiftool -T -filename -exptime -iso ...` (and FITS header keywords) populates the metadata inspector; no pixel decoding. [P1]

### 3.8 Options / Settings (`Options`)

* **Backend Settings:** Binary paths, scratch directory, cache location (`nside=64` Gaia DR3 cache), offline mode, and thread limits. These values are injected into adapter argv; they never change GUI internals. The Backends panel lists installation status and detected version for every connector, and menu sensitivity follows that status. [P1 partial]
* **Language Selection:** Interface strings (English, German, Spanish, Japanese). [P3]

## 4. Toolbars and Interactive Control Elements

Toolbars are shortcuts to the exact same actions and adapters; they add no processing behavior of their own.

* **File Action Group:** Open File (`Ctrl+O`), Save/Export, Close Active View, Print (export via backend to a print-ready raster). [P1 except Print]
* **Zoom & Navigation Group:** Zoom In/Out, Reset View, Pan/Hand — preview-only operations. [P1]
* **Analysis & Inspection Group:** Histogram button (runs the backend histogram job), Crosshair/Profile tool (backend coordinate query), Information button (opens the `exiftool`/FITS header inspector). [P1 for Information; P2/P3 for the others]
* **Dialog Parameter Controls:** When an action is invoked, the floating panel exposes the adapter's flags (sliders, spinboxes, checkboxes, format selector, backend selector, OK/Apply/Reset/Cancel). OK/Apply schedule a CLI job; Cancel terminates it. The preview checkbox requests a backend-written preview artifact, never an in-process filter. [P1]

## 5. Backend Capability Map (authoritative for adapters)

| GUI domain | CLI backend(s) | Typical artifacts |
| --- | --- | --- |
| Format conversion / export / batch | `magick`, `gm` | JPG, PNG, TIFF, BMP |
| RAW development / display stretch | `rawtherapee-cli`, `darktable-cli` | JPEG, PNG, 8/16-bit TIFF |
| Metadata / FITS headers | `exiftool` | Text tables for the inspector |
| Calibration / stacking / astrometry | `siril-cli`, `skystacker`, `astap_cli`, `solve-field` | FITS, XISF, 16/32-bit TIFF |
| Alignment / stitching / fusion | Hugin tools, `enfuse` | TIFF panoramas, HDR/focus stacks |
| Headless custom scripts / pipelines | `gimp -i -b`, `photoflow-cli`, `dcraw_emu` | TIFF/PNG outputs |

## 6. Extension Rule

To add a GUI capability: implement a CLI adapter (formats, defaults, argv serialization, missing-binary and non-zero-exit handling, scratch cleanup) with tests, then bind widgets to its flags. Any change that introduces pixel math into the GUI codebase is a violation of the zero-processing mandate and must be rejected.
