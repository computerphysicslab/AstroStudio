# Astro Studio

A zero-processing GTK desktop front-end for astronomical and photographic CLI
backends. The GUI loads and displays images, collects parameters, builds sanitized
`argv` vectors, spawns external tools asynchronously, and renders the files those
tools wrote. It never implements calibration, stacking, demosaicing, stretching or
any other pixel algorithm.

## Requirements

- Linux/Ubuntu with GTK **3.24** and PyGObject (`python3-gi`, `gir1.2-gtk-3.0`,
  `gir1.2-gdkpixbuf-2.0`).
- Python 3.8 or newer.
- Optional external binaries: `magick`, `gm`, `exiftool`, `rawtherapee-cli`,
  `darktable-cli`, `siril-cli`, `astap_cli`, `solve-field`, `gimp`, etc. Only the
  connectors installed on the host are enabled in the menu.
- `pytest` for the automated checks.

From the project root:

```bash
sudo apt install python3-gi gir1.2-gtk-3.0 gir1.2-gdkpixbuf-2.0 imagemagick libimage-exiftool-perl
```

## Run

```bash
python3 -m astrostudio
```

## Install as a desktop application

The installer is user-level (no `sudo`) and registers a launcher, icon and desktop
entry under `$XDG_DATA_HOME` (`~/.local/share` by default):

```bash
./packaging/install.sh
```

It installs `astro-studio.desktop` in `applications/`, the scalable SVG icon and
rasterized PNG sizes in `icons/hicolor/`, refreshes the desktop and icon caches, and
points the launcher at `packaging/astro-studio`. After installation, search for
**Astro Studio** in the application menu or run:

```bash
gtk-launch astro-studio
```

To verify the installation: `desktop-file-validate ~/.local/share/applications/astro-studio.desktop`.

On startup the app probes every connector binary for installation and version. The
**Backends** panel lists the result, and menu actions are enabled only when their
backend is installed and an adapter exists. A missing binary leaves the action
visible but disabled; no in-process fallback is ever attempted.

## Automated tests

```bash
python3 -m compileall -q astrostudio tests
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/ -q
```

`PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` is required in this environment because an
unrelated Dash plugin breaks pytest's autoload. The suite covers `argv`
serialization, adapter flag mapping, scratch isolation, process lifecycle
(missing binary and exit codes) and startup backend gating.

## Manual verification

1. **Startup discovery:** check the Backends panel and the terminal drawer. In the
   development environment `ExifTool` and `GIMP` are detected with their versions;
   `ImageMagick` is absent, so export actions stay disabled until it is installed.
2. **Open a file:** `Ctrl+O` (or the Open toolbar button) and select a JPG/PNG/TIFF.
   The preview renders it read-only; the status bar shows the file and dimensions.
3. **Metadata:** `Ctrl+I` (or View > FITS Header Inspector) runs `exiftool` and shows
   its output in a dialog. This works with the currently installed ExifTool.
4. **Export via CLI:** install ImageMagick, restart the app, then use File > Export /
   Save As. Optionally fill resize, unsharp, crop or rotate in the Parameter
   Inspector. The backend writes to `<scratch>/<job>/`; the app copies the result to
   your chosen destination and reloads it into the preview.
5. **Cancel a job:** start a long export and press the stop button in the toolbar.
6. **Quit:** `Ctrl+Q` cancels active jobs and removes the scratch directory.
7. **Backend settings:** Options > Backend Settings logs the full detected version
   list.

## Layout

- `astrostudio/app.py` — application, actions, accelerators, startup discovery.
- `astrostudio/core/` — command builder, async process engine, scratch manager,
  backend registry.
- `astrostudio/adapters/` — CLI connectors (ImageMagick, ExifTool).
- `astrostudio/ui/` — GTK window, menus, inspector, log drawer and preview canvas.
- `tests/` — unit and lifecycle tests.
- `packaging/` — SVG icon, `.desktop` template, launcher script and user-level installer.
- `Context/` — authoritative specifications and living AI project context.
- `roadmap.md` — milestones v0.1.0 to v1.0.0.

## Conventions

Original input files are never modified. All intermediate files live under
`<XDG_RUNTIME_DIR>/astro-studio/<session>/<job>/` (fallback
`/tmp/astro_studio_<pid>/`). CLI calls use `argv` arrays only; no shell strings and
no blocking calls on the GTK main thread.

Version control is on `main`; commit logical changes with English messages, update
`Context/AstroStudio_ai_project_context.md` and `roadmap.md` when status changes,
and never push without an explicit request.
