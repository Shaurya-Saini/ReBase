"""Train the XGBoost job-time estimator on JobLog.

Run: `python -m app.ai.train_estimator` (from backend/) → data/models/estimator.json

Prints honest cross-validated error against the naive "planned hours"
baseline. The JobLog history is synthetic (app/seed.py), so these numbers
only show the pipeline works — say so in the pitch.
"""

import numpy as np
from sqlmodel import Session, select

from app.ai.estimator import FEATURES, featurize, save
from app.config import settings
from app.db import engine
from app.models import JobLog

PARAMS = {
    "objective": "reg:squarederror",
    "max_depth": 2,
    "eta": 0.1,
    "subsample": 0.9,
    "min_child_weight": 2,
    "seed": 42,
}
ROUNDS = 150
FOLDS = 5


def _dataset(db: Session):
    logs = db.exec(select(JobLog)).all()
    X = np.array([featurize(j.machine_type, j.weather, j.operator_experience) for j in logs])
    y = np.array([j.actual_hours / j.planned_hours for j in logs])
    planned = np.array([j.planned_hours for j in logs])
    actual = np.array([j.actual_hours for j in logs])
    return X, y, planned, actual


def train(db_engine=engine, path: str | None = None, verbose: bool = True) -> dict:
    import xgboost as xgb

    with Session(db_engine) as db:
        X, y, planned, actual = _dataset(db)
    if len(y) < FOLDS * 2:
        raise RuntimeError(f"Need at least {FOLDS * 2} JobLog rows, have {len(y)}. Run `python -m app.seed`.")

    # Out-of-fold predictions → honest error + residual band for range_hours.
    rng = np.random.default_rng(42)
    fold = rng.permutation(len(y)) % FOLDS
    oof = np.zeros(len(y))
    for k in range(FOLDS):
        tr, te = fold != k, fold == k
        m = xgb.train(PARAMS, xgb.DMatrix(X[tr], label=y[tr], feature_names=FEATURES), ROUNDS)
        oof[te] = m.predict(xgb.DMatrix(X[te], feature_names=FEATURES))

    residuals = y - oof
    band = (float(np.quantile(residuals, 0.10)), float(np.quantile(residuals, 0.90)))
    metrics = {
        "rows": int(len(y)),
        "cv_mae_hours": round(float(np.mean(np.abs(planned * oof - actual))), 3),
        "baseline_mae_hours": round(float(np.mean(np.abs(planned - actual))), 3),
        "p10_p90_ratio_band": [round(band[0], 3), round(band[1], 3)],
    }

    final = xgb.train(PARAMS, xgb.DMatrix(X, label=y, feature_names=FEATURES), ROUNDS)
    save(final, band, path or settings.ESTIMATOR_PATH, metrics)
    if verbose:
        print(f"Trained on {metrics['rows']} JobLog rows → {path or settings.ESTIMATOR_PATH}")
        print(f"  CV MAE: {metrics['cv_mae_hours']} h  (planned-hours baseline: {metrics['baseline_mae_hours']} h)")
        print(f"  p10–p90 ratio band: {metrics['p10_p90_ratio_band']}")
    return metrics


if __name__ == "__main__":
    train()
