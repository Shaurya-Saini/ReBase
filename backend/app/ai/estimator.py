"""Job-time estimator (E8): XGBoost on JobLog history, with a formula fallback.

The model predicts the **ratio** actual_hours / planned_hours from
(machine_type, weather, operator_experience); the estimate is
planned_hours × ratio. Predicting a ratio lets 60 rows generalise across jobs
of different sizes.

- `range_hours` comes from out-of-fold residual quantiles (p10–p90) stored
  with the model at training time.
- `factors` are counterfactuals: how much the prediction moves versus a
  baseline of clear weather / intermediate operator. Explainable, not SHAP.
- If the model file is missing or unreadable, `FALLBACK_*` tables give the same
  shaped answer, so E8 never fails.

Train with `python -m app.ai.train_estimator` (auto-runs on server start if
the model file is missing).
"""

import json
from dataclasses import dataclass
from pathlib import Path

from app.config import settings

MACHINE_TYPES = ["excavator", "wheel_loader", "drill_rig", "dump_truck"]
WEATHERS = ["clear", "rain", "heat", "wind"]
EXPERIENCE_LEVEL = {"novice": 0, "intermediate": 1, "expert": 2}
FEATURES = [f"machine_{m}" for m in MACHINE_TYPES] + [f"weather_{w}" for w in WEATHERS] + ["experience"]

BASELINE_WEATHER = "clear"
BASELINE_EXPERIENCE = "intermediate"

# Fallback when no trained model is available (rough, hand-set).
FALLBACK_WEATHER = {"clear": 0.0, "rain": 0.12, "heat": 0.06, "wind": 0.04}
FALLBACK_EXPERIENCE = {"novice": 0.15, "intermediate": 0.0, "expert": -0.08}
FALLBACK_RESIDUALS = (-0.12, 0.12)

WEATHER_NOTE = {
    "clear": "Clear weather forecast",
    "rain": "Rain forecast",
    "heat": "High heat forecast",
    "wind": "Strong wind forecast",
}


def featurize(machine_type: str, weather: str, experience: str) -> list[float]:
    return (
        [float(machine_type == m) for m in MACHINE_TYPES]
        + [float(weather == w) for w in WEATHERS]
        + [float(EXPERIENCE_LEVEL.get(experience, 1))]
    )


@dataclass
class Factor:
    name: str
    effect_pct: int
    note: str


@dataclass
class Prediction:
    estimated_hours: float
    range_hours: tuple[float, float]
    factors: list[Factor]
    source: str  # "xgboost" | "fallback"


class Estimator:
    def __init__(self, booster=None, residuals: tuple[float, float] = FALLBACK_RESIDUALS):
        self.booster = booster
        self.residuals = residuals

    @property
    def source(self) -> str:
        return "xgboost" if self.booster is not None else "fallback"

    def ratio(self, machine_type: str, weather: str, experience: str) -> float:
        if self.booster is None:
            return 1.0 + FALLBACK_WEATHER.get(weather, 0.0) + FALLBACK_EXPERIENCE.get(experience, 0.0)
        import numpy as np
        import xgboost as xgb

        x = np.array([featurize(machine_type, weather, experience)])
        return float(self.booster.predict(xgb.DMatrix(x, feature_names=FEATURES))[0])

    def predict(self, planned_hours: float, machine_type: str, weather: str, experience: str) -> Prediction:
        r = self.ratio(machine_type, weather, experience)
        lo, hi = self.residuals
        est = planned_hours * r

        def effect(**changed) -> int:
            args = {"machine_type": machine_type, "weather": weather, "experience": experience}
            base = self.ratio(**{**args, **changed})
            return round((r / base - 1) * 100)

        machine_label = machine_type.replace("_", " ")
        factors = [
            Factor("weather", effect(weather=BASELINE_WEATHER), WEATHER_NOTE.get(weather, weather)),
            Factor("operator_experience", effect(experience=BASELINE_EXPERIENCE),
                   f"{experience.capitalize()} on {machine_label}"),
        ]
        return Prediction(
            estimated_hours=round(est, 1),
            range_hours=(round(planned_hours * max(r + lo, 0.1), 1), round(planned_hours * (r + hi), 1)),
            factors=factors,
            source=self.source,
        )


def save(booster, residuals: tuple[float, float], path: str | Path, metrics: dict) -> None:
    """Store the model + its metadata in one XGBoost JSON file."""
    booster.set_attr(rebase_meta=json.dumps({"residuals": list(residuals), "metrics": metrics,
                                             "features": FEATURES}))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    booster.save_model(str(path))


def load(path: str | Path | None = None) -> Estimator:
    path = Path(path or settings.ESTIMATOR_PATH)
    if not path.exists():
        return Estimator()
    try:
        import xgboost as xgb

        booster = xgb.Booster()
        booster.load_model(str(path))
        meta = json.loads(booster.attr("rebase_meta") or "{}")
        if meta.get("features") != FEATURES:
            return Estimator()  # stale model from an older feature set
        return Estimator(booster, tuple(meta["residuals"]))
    except Exception:  # corrupt file, missing libomp, ... → never break E8
        return Estimator()


_cache: dict[str, tuple[float, Estimator]] = {}


def get_estimator() -> Estimator:
    """Cached, but reloads if the model file changes (e.g. after re-training)."""
    path = Path(settings.ESTIMATOR_PATH)
    mtime = path.stat().st_mtime if path.exists() else -1.0
    cached = _cache.get(str(path))
    if cached is None or cached[0] != mtime:
        _cache[str(path)] = (mtime, load(path))
    return _cache[str(path)][1]
