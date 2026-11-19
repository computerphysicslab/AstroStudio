"""Time-estimation model derived from the persistent operation log."""

import json
import os
from dataclasses import dataclass
from typing import Dict, Optional


@dataclass
class StageModel:
    samples: int
    slope: float
    intercept: float

    def estimate(self, megapixels: float) -> float:
        return max(0.0, self.slope * megapixels + self.intercept)


def default_model_path() -> str:
    data_home = os.environ.get("XDG_DATA_HOME") or os.path.join(
        os.path.expanduser("~"), ".local", "share"
    )
    return os.path.join(data_home, "astro-studio", "estimates.json")


class Estimator:
    """Load an incrementally updated proportionality model for CLI operations."""

    def __init__(self, path: str = None) -> None:
        self.path = path or default_model_path()
        self.models: Dict[str, StageModel] = {}
        self.load()

    def load(self) -> None:
        try:
            with open(self.path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except (OSError, ValueError):
            return
        for stage, values in data.get("models", {}).items():
            self.models[stage] = StageModel(
                samples=int(values.get("samples", 0)),
                slope=float(values.get("slope", 0.0)),
                intercept=float(values.get("intercept", 0.0)),
            )

    def estimate(self, stage: str, megapixels: float) -> Optional[float]:
        model = self.models.get(stage)
        if model is None or model.samples == 0 or megapixels <= 0:
            return None
        value = model.estimate(megapixels)
        return value if value > 0 else None

    def summary(self) -> Dict[str, int]:
        return {stage: model.samples for stage, model in self.models.items()}
