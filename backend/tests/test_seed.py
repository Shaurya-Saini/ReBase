"""B1: seed produces the demo cast and a learnable JobLog signal."""

from datetime import datetime, timedelta, timezone
from statistics import mean

import pytest
from sqlmodel import Session, create_engine, select

from app.config import settings
from app.models import Assignment, Job, JobLog, Machine, Operator, Project, WorkSession
from app.seed import IST, seed

NOW = datetime(2026, 9, 24, 6, 0, tzinfo=timezone.utc)  # 11:30 IST


@pytest.fixture
def db(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/seed.db")
    seed(engine, now=NOW)
    with Session(engine) as s:
        yield s


def test_counts(db):
    assert len(db.exec(select(Operator)).all()) == 5
    assert {m.type for m in db.exec(select(Machine)).all()} == {
        "excavator", "wheel_loader", "drill_rig", "dump_truck"}
    assert len(db.exec(select(Project)).all()) == 2
    assert len(db.exec(select(Job)).all()) == 8
    assert len(db.exec(select(JobLog)).all()) == 60


def test_contract_example_ids_exist(db):
    ravi = db.get(Operator, "op_001")
    assert ravi.name == "Ravi Kumar" and ravi.lang == "ta-IN"
    assert ravi.experience["excavator"] == "expert"
    assert db.get(Machine, "mc_001").serial == "EX20-0001"
    job = db.get(Job, "job_001")
    assert job.title == "Trench excavation – Block C" and job.planned_hours == 6.0
    assert job.scheduled_start == datetime(2026, 9, 24, 3, 30, tzinfo=timezone.utc)  # 09:00 IST


def test_languages_cover_demo(db):
    assert {o.lang for o in db.exec(select(Operator)).all()} == {"en-IN", "hi-IN", "ta-IN"}


def test_assignments_match_machine_type(db):
    for a in db.exec(select(Assignment)).all():
        assert db.get(Machine, a.machine_id).type == db.get(Job, a.job_id).machine_type
    today = NOW.astimezone(IST).date()
    ravi = db.exec(select(Assignment).where(Assignment.operator_id == "op_001")).all()
    assert today in {a.date for a in ravi}


def _hours_7d(db, op_id):
    since = NOW - timedelta(days=7)
    rows = db.exec(select(WorkSession).where(WorkSession.operator_id == op_id)).all()
    return sum((s.ended_at - s.started_at).total_seconds() / 3600
               for s in rows if s.ended_at > since)


def test_fatigue_cast(db):
    assert _hours_7d(db, "op_001") == pytest.approx(41.0)
    assert _hours_7d(db, "op_002") == pytest.approx(52.0)
    assert _hours_7d(db, "op_002") < settings.MAX_HOURS_7D
    # Mohit's last shift was a full 12 h and ended only 4 h ago.
    last = max(db.exec(select(WorkSession).where(WorkSession.operator_id == "op_004")).all(),
               key=lambda s: s.ended_at)
    assert (last.ended_at - last.started_at) == timedelta(hours=settings.MAX_SHIFT_HOURS)
    assert NOW - last.ended_at < timedelta(hours=settings.MIN_REST_HOURS)


def test_history_is_in_the_past_and_ended(db):
    for s in db.exec(select(WorkSession)).all():
        assert s.state == "ended" and s.started_at < s.ended_at <= NOW


@pytest.mark.parametrize("ist_hour", range(24))
def test_history_valid_whenever_seeded(ist_hour):
    """The demo may be re-seeded at any hour: no future work, no overlapping shifts."""
    from app.seed import _work_history

    now = datetime(2026, 9, 24, ist_hour, 0, tzinfo=IST).astimezone(timezone.utc)
    by_op: dict[str, list] = {}
    for op, start, end in _work_history(now, now.astimezone(IST).date()):
        assert end <= now
        by_op.setdefault(op, []).append((start, end))
    for spans in by_op.values():
        spans.sort()
        assert all(s2 >= e1 for (_, e1), (s2, _) in zip(spans, spans[1:]))


def test_joblog_has_learnable_signal(db):
    logs = db.exec(select(JobLog)).all()

    def ratio(pred):
        return mean(log.actual_hours / log.planned_hours for log in logs if pred(log))

    assert {log.weather for log in logs} >= {"clear", "rain"}
    assert {log.operator_experience for log in logs} == {"novice", "intermediate", "expert"}
    assert ratio(lambda log: log.operator_experience == "novice") > \
        ratio(lambda log: log.operator_experience == "expert") + 0.1
    assert ratio(lambda log: log.weather == "rain") > ratio(lambda log: log.weather == "clear")


def test_deterministic(tmp_path):
    def snapshot(name):
        engine = create_engine(f"sqlite:///{tmp_path}/{name}.db")
        seed(engine, now=NOW)
        with Session(engine) as s:
            return [(j.operator_id, j.actual_hours, j.date) for j in s.exec(select(JobLog)).all()]

    assert snapshot("a") == snapshot("b")


def test_reseed_wipes(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path}/twice.db")
    seed(engine, now=NOW)
    seed(engine, now=NOW)
    with Session(engine) as s:
        assert len(s.exec(select(JobLog)).all()) == 60
