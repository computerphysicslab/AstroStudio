"""SkyStacker connector for plate solving, Gaia sky maps and survey cutouts.

Contract: docs/plate-solving.md and docs/astrometry-products.md of the SkyStacker
project. Only ``--process-image`` single-image mode is used so originals are never
modified and all products stay in the requested output directory.
"""

from typing import List

from ..core.command_builder import CommandBuilder
from .base import CliAdapter


class SkyStackerAdapter(CliAdapter):
    name = "SkyStacker"
    binary = "skystacker"
    description = "Plate solving, layered Gaia SVG maps and HiPS survey cutouts"
    input_formats = ("jpg", "jpeg", "png", "fits", "fit", "tif", "tiff")

    def __init__(self) -> None:
        super().__init__(CommandBuilder(self.binary))

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

    @staticmethod
    def _solver_flags(
        solver: str,
        plate_center: str,
        offline: bool,
        timeout: int,
        focal_length: str,
        pixel_size: str,
    ) -> List[str]:
        flags = ["--plate-solver", solver or "auto", "--astrometry-timeout", str(timeout)]
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
        return argv

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
        return argv

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
        return argv
