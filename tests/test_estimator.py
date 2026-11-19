"""Time estimator tests."""

import json

from astrostudio.core.estimator import Estimator


def test_estimator_uses_persisted_proportionality_model(tmp_path):
    path = str(tmp_path / "estimates.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(
            {
                "models": {
                    "resize": {"samples": 4, "slope": 0.5, "intercept": 0.2},
                    "empty": {"samples": 0, "slope": 1.0, "intercept": 1.0},
                }
            },
            handle,
        )
    estimator = Estimator(path)
    assert estimator.estimate("resize", 2.0) == 1.2
    assert estimator.estimate("empty", 2.0) is None
    assert estimator.estimate("unknown", 2.0) is None
    assert estimator.summary()["resize"] == 4
