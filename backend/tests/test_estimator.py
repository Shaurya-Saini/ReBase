"""B6: XGBoost estimator (training, fallback) and E8."""

from datetime import date

import pytest
from sqlmodel import create_engine

from app.ai import estimator as est_mod
from app.ai.estimator import Estimator, load
from app.ai.train_estimator import train
from app.seed import seed


@pytest.fixture(scope="module")
def trained(tmp_path_factory):
    d = tmp_path_factory.mktemp("est")
    engine = create_engine(f"sqlite:///{d}/db.db")
    seed(engine)
    path = d / "estimator.json"
    metrics = train(engine, str(path), verbose=False)
    return path, metrics


def test_training_beats_planned_hours_baseline(trained):
    _, m = trained
    assert m["rows"] == 60
    assert m["cv_mae_hours"] < 0.5 * m["baseline_mae_hours"]
    lo, hi = m["p10_p90_ratio_band"]
    assert lo < 0 < hi


def test_model_learned_the_signal(trained):
    e = load(trained[0])
    assert e.source == "xgboost"
    assert e.ratio("excavator", "rain", "intermediate") > e.ratio("excavator", "clear", "intermediate") + 0.05
    assert e.ratio("excavator", "clear", "novice") > e.ratio("excavator", "clear", "expert") + 0.1


def test_prediction_shape(trained):
    p = load(trained[0]).predict(6.0, "excavator", "rain", "expert")
    lo, hi = p.range_hours
    assert lo < p.estimated_hours < hi
    by_name = {f.name: f for f in p.factors}
    assert by_name["weather"].effect_pct > 0 and by_name["weather"].note == "Rain forecast"
    assert by_name["operator_experience"].effect_pct < 0
    assert by_name["operator_experience"].note == "Expert on excavator"


def test_fallback_when_model_missing(tmp_path):
    e = load(tmp_path / "nope.json")
    assert e.source == "fallback"
    p = e.predict(10.0, "drill_rig", "rain", "novice")
    assert p.estimated_hours == pytest.approx(12.7)
    assert p.range_hours[0] < p.estimated_hours < p.range_hours[1]


def test_fallback_when_model_corrupt(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not a model")
    assert load(bad).source == "fallback"


def test_clear_intermediate_has_zero_effects():
    p = Estimator().predict(5.0, "excavator", "clear", "intermediate")
    assert [f.effect_pct for f in p.factors] == [0, 0] and p.estimated_hours == 5.0


def test_get_estimator_reloads_after_retrain(trained, monkeypatch, tmp_path):
    path = tmp_path / "m.json"
    monkeypatch.setattr(est_mod.settings, "ESTIMATOR_PATH", str(path))
    assert est_mod.get_estimator().source == "fallback"
    path.write_bytes(trained[0].read_bytes())
    assert est_mod.get_estimator().source == "xgboost"


# ---------- E8 ----------

def test_e8_job_001(client):
    r = client.get("/jobs/job_001/estimate")
    assert r.status_code == 200
    e = r.json()
    assert e["job_id"] == "job_001"
    lo, hi = e["range_hours"]
    assert lo < e["estimated_hours"] < hi
    # rain + expert Ravi: weather pushes up, experience pulls down
    f = {x["name"]: x for x in e["factors"]}
    assert f["weather"]["effect_pct"] > 0 and f["operator_experience"]["effect_pct"] < 0
    assert f["operator_experience"]["note"] == "Expert on excavator"
    assert date.fromisoformat(e["project_completion_date"]) >= date.fromisoformat(
        client.get("/jobs/job_001").json()["scheduled_start"][:10])


def test_e8_novice_job_estimates_longer(client):
    # job_008 (dump truck, rain) is assigned to novice Arjun
    e = client.get("/jobs/job_008/estimate").json()
    assert e["estimated_hours"] > 8.0
    assert {x["name"]: x for x in e["factors"]}["operator_experience"]["note"] == "Novice on dump truck"


def test_e8_unknown_job(client):
    r = client.get("/jobs/job_999/estimate")
    assert r.status_code == 404 and r.json()["error"]["code"] == "JOB_NOT_FOUND"
