"""Direct external blind solvers used when SkyStacker's solver chain is unavailable."""

import os
from typing import List


def scale_hint_arcsec(focal_length: str, pixel_size: str) -> float:
    """Return arcsec/pixel from focal length (mm) and pixel size (um)."""
    return float(pixel_size) / float(focal_length) * 206.26


class AstrometryAdapter:
    """Build argv for ``solve-field`` or ``astap`` without shell strings."""

    def __init__(self, binary: str) -> None:
        self.binary = binary

    @property
    def name(self) -> str:
        return "Astrometry.net" if "solve-field" in self.binary else "ASTAP"

    def is_available(self) -> bool:
        import shutil

        return shutil.which(self.binary) is not None

    def build_solve_field_argv(
        self,
        image: str,
        output_dir: str,
        ra: str = None,
        dec: str = None,
        scale: str = None,
    ) -> List[str]:
        argv = [
            self.binary,
            "--no-plots",
            "--overwrite",
            "--new-dir",
            "-D",
            output_dir,
        ]
        if ra and dec:
            argv.extend(("--ra", str(ra), "--dec", str(dec)))
        if scale:
            value = float(scale)
            argv.extend(
                (
                    "--scale-units",
                    "arcsecperpix",
                    "--scale-low",
                    str(value * 0.8),
                    "--scale-high",
                    str(value * 1.2),
                )
            )
        argv.append(image)
        return argv

    def build_astap_argv(self, image: str, output_dir: str, fov: str = None) -> List[str]:
        argv = [self.binary, "-f", image, "-D", output_dir]
        if fov:
            argv.extend(("-fov", str(fov)))
        return argv
