"""B3: fatigue rules (E4 hours + rest) and the E10 REST_REQUIRED gate."""

from datetime import datetime, timedelta, timezone

import pytest
from sqlmodel import Session, create_engine

from app.clock import IST
from app.models import Operator, WorkSession
from app.seed import seed
from app.services.fatigue import current_shift, hours_in_window, operator_fatigue

T0 = datetime(2026, 9, 24, 6, 0, tzinfo=timezone.utc)
H = timedelta(hours=1)

STORY = {"op_001": "ok", "op_002": "warning", "op_003": "ok", "op_004": "must_rest", "op_005": "ok"}


# ---------- pure helpers ----------

def test_current_shift_joins_short_breaks_and_splits_on_full_rest():
    ivs = [(T0 - 30 * H, T0 - 22 * H),          # old shift
           (T0 - 8 * H, T0 - 5 * H), (T0 - 4 * H, T0 - 1 * H)]  # today, 1 h break
    assert current_shift(ivs, T0) == ivs[1:]
    assert current_shift(ivs, T0 + 8 * H) == ivs[1:]      # 9 h after end → still resting
    assert current_shift(ivs, T0 + 9 * H) == []           # 10 h after end → fully rested


def test_hours_in_window_clips():
    ivs = [(T0 - 10 * H, T0 - 6 * H)]
    assert hours_in_window(ivs, T0 - 8 * H, T0) == pytest.approx(2)


# ---------- rules on a hand-built history ----------

@pytest.fixture
def db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/f.db")
    from sqlmodel import SQLModel

    from app import models  # noqa: F401
    SQLModel.metadata.create_all(engine)
    with Session(engine) as s:
        s.add(Operator(id="op_x", name="X", lang="en-IN", pin="1", experience={}))
        s.commit()
        yield s


def _work(db, *spans):
    for i, (a, b) in enumerate(spans):
        db.add(WorkSession(id=f"ses_t{i}", operator_id="op_x", machine_id="mc_001", job_id="job_001",
                           state="ended" if b else "active", created_at=a, started_at=a, ended_at=b))
    db.commit()


def _f(db, now=T0):
    return operator_fatigue(db, db.get(Operator, "op_x"), now)


def test_no_work_is_ok(db):
    f = _f(db)
    assert (f.hours_today, f.hours_7d, f.rest["status"]) == (0, 0, "ok")


def test_long_shift_warning_then_must_rest(db):
    _work(db, (T0 - 10 * H, T0))
    assert _f(db).rest["status"] == "warning"  # 10 h ≥ 9.6 h
    db.get(WorkSession, "ses_t0").started_at = T0 - 12 * H
    db.commit()
    f = _f(db)
    assert f.rest["status"] == "must_rest"
    assert f.rest["next_allowed_start"] == T0 + 10 * H
    assert "Shift limit" in f.rest["reason"]
    assert _f(db, T0 + 10 * H).rest["status"] == "ok"  # rested → new shift allowed


def test_active_session_counts_to_now(db):
    _work(db, (T0 - 3 * H, None))
    assert _f(db).hours_today == pytest.approx(3)


def test_weekly_cap(db):
    # 6 days × 10 h, each on a separate day → 60 h in 7 days, short shifts.
    _work(db, *[(T0 - d * 24 * H - 12 * H, T0 - d * 24 * H - 2 * H) for d in range(1, 7)])
    f = _f(db)
    assert f.hours_7d == pytest.approx(60) and f.hours_today == 0
    assert f.rest["status"] == "must_rest" and "7-day" in f.rest["reason"]
    # clears once the oldest day starts rolling out of the window
    assert T0 < f.rest["next_allowed_start"] <= T0 + 24 * H
    assert _f(db, f.rest["next_allowed_start"]).rest["status"] != "must_rest"


def test_weekly_warning(db):
    _work(db, *[(T0 - d * 24 * H - 11 * H, T0 - d * 24 * H - 2.5 * H) for d in range(1, 7)])
    f = _f(db)  # 6 × 8.5 = 51 h
    assert f.rest["status"] == "warning" and "weekly" in f.rest["reason"]


# ---------- the seeded demo cast holds at every hour ----------

@pytest.mark.parametrize("ist_hour", range(24))
def test_demo_story_any_time_of_day(tmp_path, ist_hour):
    now = datetime(2026, 9, 24, ist_hour, 15, tzinfo=IST).astimezone(timezone.utc)
    engine = create_engine(f"sqlite:///{tmp_path}/demo.db")
    seed(engine, now=now)
    with Session(engine) as s:
        got = {op: operator_fatigue(s, s.get(Operator, op), now).rest["status"] for op in STORY}
        ravi = operator_fatigue(s, s.get(Operator, "op_001"), now)
    assert got == STORY
    assert ravi.hours_today == pytest.approx(3.5) and ravi.hours_7d == pytest.approx(41)


# ---------- API ----------

def test_e4_reports_real_hours(client):
    ravi = client.get("/operators/op_001").json()
    assert ravi["hours_today"] == 3.5 and ravi["hours_7d"] == 41.0
    assert ravi["rest"] == {"status": "ok", "next_allowed_start": None, "reason": None}
    mohit = client.get("/operators/op_004").json()["rest"]
    assert mohit["status"] == "must_rest" and mohit["next_allowed_start"].endswith("Z")
    assert client.get("/operators/op_002").json()["rest"]["status"] == "warning"


def test_e10_gate(client):
    r = client.post("/sessions", json={"operator_id": "op_004", "machine_id": "mc_004", "job_id": "job_004"})
    assert r.status_code == 409
    e = r.json()["error"]
    assert e["code"] == "REST_REQUIRED" and e["next_allowed_start"].endswith("Z")
    ok = client.post("/sessions", json={"operator_id": "op_001", "machine_id": "mc_001", "job_id": "job_001"})
    assert ok.status_code == 201
    r = client.post("/sessions", json={"operator_id": "op_999", "machine_id": "mc_001", "job_id": "job_001"})
    assert r.status_code == 404
