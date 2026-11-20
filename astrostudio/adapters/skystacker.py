"""SkyStacker connector for plate solving, Gaia sky maps and survey cutouts.

Contract: docs/plate-solving.md and docs/astrometry-products.md of the SkyStacker
project. Only ``--process-image`` single-image mode is used so originals are never
modified and all products stay in the requested output directory.
"""

import os
from typing import List

from ..core.command_builder import CommandBuilder
from .base import CliAdapter


def discover_catalog_dir() -> str:
    """Locate a SkyStacker blind-catalog directory with a manifest."""
    home = os.path.expanduser("~")
    candidates = [
        os.path.join(home, "datos", "datos-juan", "proyectos", "astronomia", "SkyStacker", "catalogs"),
        os.path.join(home, "proyectos", "astronomia", "SkyStacker", "catalogs"),
        os.environ.get("SKYSTACKER_CATALOGS", ""),
    ]
    for candidate in candidates:
        if candidate and os.path.isfile(os.path.join(candidate, "manifest.json")):
            return candidate
    return ""


class SkyStackerAdapter(CliAdapter):
    name = "SkyStacker"
    binary = "skystacker"
    description = "Plate solving, layered Gaia SVG maps and HiPS survey cutouts"
    input_formats = (
        "jpg",
        "jpeg",
        "png",
        "fits",
        "fit",
        "tif",
        "tiff",
        "cr2",
        "cr3",
        "ser",
        "pgm",
        "ppm",
        "xisf",
    )

    def __init__(self) -> None:
        super().__init__(CommandBuilder(self.binary))
        self.cache_dir = None
        self.catalog_dir = None
        self.gaia_nside = 64
        self.blind_catalog = "mag07"

    @staticmethod
    def _base(source: str, image_op: str, output_dir: str) -> List[str]:
        return [
            "skystacker",
            "--process-image",
            source,
            "--image-op",
            image_op,
            "--image-output",
            output_dir,
            "--no-donation",
        ]

    def _solver_flags(
        self,
        solver: str,
        plate_center: str,
        offline: bool,
        timeout: int,
        focal_length: str,
        pixel_size: str,
    ) -> List[str]:
        flags = [
            "--plate-solver",
            solver or "auto",
            "--astrometry-timeout",
            str(timeout),
            "--gaia-nside",
            str(int(self.gaia_nside)),
        ]
        if self.cache_dir:
            flags.extend(("--gaia-cache-dir", self.cache_dir))
        if plate_center:
            flags.extend(("--plate-center", plate_center))
        if offline:
            flags.append("--gaia-offline")
        if focal_length and pixel_size:
            flags.extend(
                (
                    "--solver-focal-length",
                    str(focal_length),
                    "--solver-pixel-size",
                    str(pixel_size),
                )
            )
        return flags

    def _with_catalog_env(self, argv: List[str]) -> List[str]:
        if not self.catalog_dir:
            return argv
        return ["/usr/bin/env", "SKYSTACKER_CATALOGS=" + self.catalog_dir] + argv

    def build_plate_solve_argv(
        self,
        source: str,
        output_dir: str,
        plate_center: str = None,
        solver: str = "auto",
        offline: bool = False,
        timeout: int = 180,
        focal_length: str = None,
        pixel_size: str = None,
    ) -> List[str]:
        argv = self._base(source, "plate-solve", output_dir)
        argv.extend(
            self._solver_flags(
                solver, plate_center, offline, timeout, focal_length, pixel_size
            )
        )
        if self.catalog_dir and solver != "native":
            argv.extend(("--blind-catalog", self.blind_catalog))
        return self._with_catalog_env(argv)

    def build_sky_map_argv(
        self,
        source: str,
        output_dir: str,
        plate_center: str = None,
        solver: str = "auto",
        offline: bool = False,
        timeout: int = 180,
        focal_length: str = None,
        pixel_size: str = None,
    ) -> List[str]:
        argv = self._base(source, "sky-map", output_dir)
        argv.append("--plate-solve")
        argv.extend(
            self._solver_flags(
                solver, plate_center, offline, timeout, focal_length, pixel_size
            )
        )
        if self.catalog_dir and solver != "native":
            argv.extend(("--blind-catalog", self.blind_catalog))
        return self._with_catalog_env(argv)

    def build_blind_solve_argv(
        self,
        source: str,
        output_dir: str,
        catalog: str = "mag07",
        blind_index: str = None,
        focal_length: str = None,
        pixel_size: str = None,
    ) -> List[str]:
        """Wide-field offline solve using SkyStacker's native Gaia quad index."""
        argv = self._base(source, "plate-solve", output_dir)
        argv.extend(("--plate-solver", "native"))
        if blind_index:
            argv.extend(("--blind-index", blind_index))
        elif catalog:
            argv.extend(("--blind-catalog", catalog))
        if focal_length and pixel_size:
            argv.extend(
                (
                    "--solver-focal-length",
                    str(focal_length),
                    "--solver-pixel-size",
                    str(pixel_size),
                )
            )
        if self.catalog_dir:
            return [
                "/usr/bin/env",
                "SKYSTACKER_CATALOGS=" + self.catalog_dir,
            ] + argv
        return argv

    @staticmethod
    def build_export_stars_argv(source: str, output_file: str) -> List[str]:
        """Export flux-sorted star detections without plate solving."""
        return [
            "skystacker",
            "--process-image",
            source,
            "--export-stars",
            output_file,
            "--no-donation",
        ]

    @staticmethod
    def build_classify_objects_argv(source: str, output_file: str) -> List[str]:
        """Report-only diffuse-object classification with IVOA object types."""
        return [
            "skystacker",
            "--process-image",
            source,
            "--classify-objects",
            output_file,
            "--no-donation",
        ]

    @staticmethod
    def build_image_op_argv(
        source: str,
        output_dir: str,
        image_op: str,
        flags: List[str] = None,
    ) -> List[str]:
        """Build a single-image transform argv (no stacking, no original writes)."""
        argv = SkyStackerAdapter._base(source, image_op, output_dir)
        if flags:
            argv.extend(flags)
        return argv

    @staticmethod
    def find_image_product(output_dir: str, image_op: str) -> str:
        """Locate the JPEG product written by an image-op job."""
        if not os.path.isdir(output_dir):
            return ""
        matches = sorted(
            name
            for name in os.listdir(output_dir)
            if name.lower().endswith((".jpg", ".jpeg", ".png")) and "_" + image_op in name
        )
        return os.path.join(output_dir, matches[0]) if matches else ""

    @staticmethod
    def build_bpm_argv(source_dir: str, output_dir: str, sigma: float = 5.0) -> List[str]:
        return [
            "skystacker",
            source_dir,
            "--output",
            output_dir,
            "--overwrite",
            "--bpm-auto",
            "--bpm-auto-sigma",
            str(sigma),
            "--stack-only",
            "--no-donation",
        ]

    @staticmethod
    def build_raw_import_argv(source_dir: str, output_dir: str) -> List[str]:
        """Stack a single CR2 into a 32-bit float TIFF using the native decoder."""
        return [
            "skystacker",
            source_dir,
            "--output",
            output_dir,
            "--overwrite",
            "--tiff",
            "--no-postprocess",
            "--no-register",
            "--workers",
            "2",
            "--no-donation",
        ]

    def build_survey_cutout_argv(
        self,
        source: str,
        output_dir: str,
        survey: str = None,
        plate_center: str = None,
        solver: str = "auto",
        offline: bool = False,
        timeout: int = 180,
    ) -> List[str]:
        argv = self._base(source, "survey-cutout", output_dir)
        argv.append("--plate-solve")
        argv.extend(self._solver_flags(solver, plate_center, offline, timeout, None, None))
        if survey:
            argv.extend(("--survey-hips", survey))
        if self.catalog_dir and solver != "native":
            argv.extend(("--blind-catalog", self.blind_catalog))
        return self._with_catalog_env(argv)
