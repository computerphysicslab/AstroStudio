"""SkyStacker connector for plate solving, Gaia maps and survey cutouts."""

from typing import List

from ..core.command_builder import CommandBuilder
from .base import CliAdapter


class SkyStackerAdapter(CliAdapter):
    name = "SkyStacker"
    binary = "skystacker"
    description = "Plate solving, Gaia sky maps and HiPS survey cutouts"
    input_formats = ("jpg", "jpeg", "png", "fits", "fit")

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

    def build_plate_solve_argv(
        self, source: str, output_dir: str, plate_center: str = None, offline: bool = False
    ) -> List[str]:
        argv = self._base(source, "measure-quality", output_dir)
        argv.extend(("--plate-solve", "--json-report"))
        if plate_center:
            argv.extend(("--plate-center", plate_center))
        if offline:
            argv.append("--gaia-offline")
        return argv

    def build_sky_map_argv(
        self, source: str, output_dir: str, offline: bool = False
    ) -> List[str]:
        argv = self._base(source, "sky-map", output_dir)
        if offline:
            argv.append("--gaia-offline")
        return argv

    def build_survey_cutout_argv(
        self, source: str, output_dir: str, survey: str = None
    ) -> List[str]:
        argv = self._base(source, "survey-cutout", output_dir)
        if survey:
            argv.extend(("--survey-hips", survey))
        return argv
