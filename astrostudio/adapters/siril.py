"""Siril connector for calibration and stacking (requires siril-cli)."""

from typing import List

from ..core.command_builder import CommandBuilder
from .base import CliAdapter


class SirilAdapter(CliAdapter):
    name = "Siril"
    binary = "siril-cli"
    description = "Master calibration frames and basic stacking via Siril scripts"
    input_formats = ("fits", "fit", "cr2", "cr3", "nef", "arw", "tif", "tiff")

    def __init__(self) -> None:
        super().__init__(CommandBuilder(self.binary))

    def build_script_argv(self, script_path: str) -> List[str]:
        return [self.binary, "-s", script_path]

    @staticmethod
    def calibration_script(
        lights: str, darks: str, flats: str, biases: str, output: str, method: str = "median"
    ) -> str:
        lines = [
            "requires siril-cli 1.2+",
            "cd \"%s\"" % lights,
        ]
        if biases:
            lines += [
                "cd \"%s\"" % biases,
                "calibrate bias",
                "stack %s bias_stacked" % method,
            ]
        if darks:
            lines += [
                "cd \"%s\"" % darks,
                "calibrate dark",
                "stack %s dark_stacked" % method,
            ]
        if flats:
            lines += [
                "cd \"%s\"" % flats,
                "calibrate flat",
                "stack %s flat_stacked" % method,
            ]
        lines += [
            "cd \"%s\"" % lights,
            "calibrate light",
            "stack %s result" % method,
            "cd \"%s\"" % output,
        ]
        return "\n".join(lines) + "\n"

    @staticmethod
    def stacking_script(lights: str, output: str, method: str = "median") -> str:
        return "\n".join(
            [
                "requires siril-cli 1.2+",
                "cd \"%s\"" % lights,
                "stack %s result" % method,
                "cd \"%s\"" % output,
            ]
        ) + "\n"
