# Optional runtime dependencies

Astro Studio always needs GTK 3.24, PyGObject, GdkPixbuf and ImageMagick 6 for previews.
Every other backend is optional; a missing binary only disables its menu actions.

| Backend | Binary | Apt package | Purpose |
| --- | --- | --- | --- |
| ExifTool | `exiftool` | `libimage-exiftool-perl` | read-only metadata |
| SkyStacker | `skystacker` | source build | stacking, astrometry, filters, catalogs |
| Siril | `siril-cli` | `siril` | calibration scripts and stacking |
| ASTAP | `astap_cli` | `astap` | plate solving |
| Astrometry.net | `solve-field` | `astrometry.net` | plate solving with index files |
| RawTherapee | `rawtherapee-cli` | `rawtherapee` | RAW development |
| darktable | `darktable-cli` | `darktable` | RAW development |
| GIMP | `gimp` | `gimp` | Script-Fu batch jobs |
| Hugin | `enblend` | `hugin` | panorama assembly |
| Enfuse | `enfuse` | `enfuse` | exposure fusion |
| FFmpeg | `ffmpeg` | `ffmpeg` | SER/AVI extraction |
| gzip | `gzip` | coreutils | FITS `.gz` export |

Bundled catalog data: OpenNGC (CC BY-SA 4.0), see `astrostudio/data/CREDITS.md`.
