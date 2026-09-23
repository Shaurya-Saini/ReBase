"""Demo data. Run: `python -m app.seed` (from backend/) → wipes and refills the DB.

Everything is relative to the moment the seed runs ("today" = the IST calendar
day), so the demo works on any date. Re-seed right before a demo.

Demo cast (IDs match the CONTRACT.md §4 examples where they overlap):

| Operator | Lang  | Story                                                        |
|----------|-------|--------------------------------------------------------------|
| op_001 Ravi Kumar    | ta-IN | Hero. Excavator expert. ~3.5 h so far today (short break now), ~41 h in 7 days → rest **ok** |
| op_002 Priya Sharma  | hi-IN | Loader expert. ~52 h in 7 days → rest **warning** (close to the 60 h cap) |
| op_003 Arjun Murugan | ta-IN | Novice, light week → rest **ok**. Good for the Training Hub story |
| op_004 Mohit Verma   | hi-IN | Finished a 12 h night shift ~4 h ago → **must_rest** (E10 gate demo) |
| op_005 Sam D'Souza   | en-IN | Drill rig / truck, intermediate → rest **ok**. English fallback |

Work history for the fatigue service (B3) is stored as ended sessions. Intended
rule for B3: sessions separated by less than MIN_REST_HOURS belong to the same
shift; a new shift may only start after MIN_REST_HOURS of rest.

JobLog: 60 past jobs whose actual/planned ratio depends on weather, operator
experience and machine type (+ noise), so the XGBoost estimator (B6) has a
real signal to learn. The data is synthetic; say so in the pitch.
"""

import random
from datetime import date, datetime, time, timedelta, timezone

from sqlmodel import Session, SQLModel

from app.clock import IST
from app.db import engine
from app.models import (
    Assignment,
    Job,
    JobLog,
    Machine,
    Operator,
    Project,
    WorkSession,
)

DAY_SHIFT_START = time(9, 0)  # IST (03:30 UTC)
NIGHT_SHIFT_START = time(21, 0)  # IST (15:30 UTC)

DEMO_PINS = {"op_001": "1234", "op_002": "2345", "op_003": "3456", "op_004": "4567", "op_005": "5678"}

# Ground-truth effects used to synthesise JobLog (the estimator should roughly
# recover these). Multiplicative on planned_hours.
WEATHER_EFFECT = {"clear": 0.00, "rain": 0.15, "heat": 0.07, "wind": 0.05}
EXPERIENCE_EFFECT = {"novice": 0.18, "intermediate": 0.05, "expert": -0.06}
MACHINE_EFFECT = {"excavator": 0.00, "wheel_loader": -0.02, "drill_rig": 0.08, "dump_truck": 0.03}
WEATHER_WEIGHTS = {"clear": 0.5, "rain": 0.2, "heat": 0.2, "wind": 0.1}


def to_utc(dt: datetime) -> datetime:
    """DB convention: timezone-aware datetimes in UTC."""
    return dt.astimezone(timezone.utc)


def shift_start(day: date, shift: str) -> datetime:
    t = DAY_SHIFT_START if shift == "day" else NIGHT_SHIFT_START
    return to_utc(datetime.combine(day, t, tzinfo=IST))


# ---------- static reference data ----------

OPERATORS = [
    ("op_001", "Ravi Kumar", "ta-IN", {"excavator": "expert", "wheel_loader": "novice"}),
    ("op_002", "Priya Sharma", "hi-IN", {"wheel_loader": "expert", "dump_truck": "intermediate"}),
    ("op_003", "Arjun Murugan", "ta-IN", {"excavator": "novice", "dump_truck": "novice"}),
    ("op_004", "Mohit Verma", "hi-IN", {"dump_truck": "expert", "excavator": "intermediate"}),
    ("op_005", "Sam D'Souza", "en-IN", {"drill_rig": "intermediate", "dump_truck": "intermediate"}),
]

MACHINES = [
    ("mc_001", "excavator", "Generic 20t Excavator", "EX20-0001", 4521.3),
    ("mc_002", "wheel_loader", "Generic 3.5 m³ Wheel Loader", "WL35-0002", 3187.6),
    ("mc_003", "drill_rig", "Generic Crawler Drill Rig", "DR90-0003", 2204.9),
    ("mc_004", "dump_truck", "Generic 40t Articulated Dump Truck", "DT40-0004", 6012.4),
]
MACHINE_BY_TYPE = {t: mid for mid, t, *_ in MACHINES}

PROJECTS = [
    ("prj_001", "North Pit Expansion", "Site 2, North Pit", 25),
    ("prj_002", "Highway Cut – Section 4", "NH-44 Cut, Section 4", 40),
]

# (id, project, title, site, machine_type, day_offset, shift, planned_hours, weather, hazards)
JOBS = [
    ("job_001", "prj_001", "Trench excavation – Block C", "Site 2, North Pit", "excavator", 0, "day", 6.0, "rain",
     ["Overhead power line near east edge", "Soft ground after rain"]),
    ("job_002", "prj_001", "Stockpile loading – Bay 3", "Site 2, North Pit", "wheel_loader", 0, "day", 7.0, "clear",
     ["Busy haul road crossing at Bay 3 exit"]),
    ("job_003", "prj_001", "Blast-hole drilling – Bench 5", "Site 2, North Pit", "drill_rig", 1, "day", 8.0, "heat",
     ["Bench edge within 5 m", "High dust — keep cab sealed"]),
    ("job_004", "prj_001", "Overburden haul to Dump B", "Site 2, North Pit", "dump_truck", 0, "night", 10.0, "clear",
     ["Night haul — reduced visibility on ramp 2"]),
    ("job_005", "prj_002", "Drainage ditch – Ch. 4+200 to 4+450", "NH-44 Cut, Section 4", "excavator", 2, "day", 5.5, "clear",
     ["Live traffic 8 m from work zone"]),
    ("job_006", "prj_002", "Subgrade loading – Ch. 4+500", "NH-44 Cut, Section 4", "wheel_loader", 5, "day", 6.5, "wind",
     ["Wind-blown dust across carriageway"]),
    ("job_007", "prj_002", "Rock cut drilling – Ch. 4+800", "NH-44 Cut, Section 4", "drill_rig", 9, "day", 9.0, "clear",
     ["Loose rock on upper face"]),
    ("job_008", "prj_002", "Spoil haul to disposal yard", "NH-44 Cut, Section 4", "dump_truck", 16, "day", 8.0, "rain",
     ["Slippery unpaved haul road when wet"]),
]

# (assignment id, operator, job). Machine = the machine of the job's type.
ASSIGNMENTS = [
    ("asg_001", "op_001", "job_001"),  # today — the demo job
    ("asg_002", "op_002", "job_002"),  # today
    ("asg_003", "op_004", "job_004"),  # tonight — Mohit is still resting
    ("asg_004", "op_005", "job_003"),  # tomorrow
    ("asg_005", "op_001", "job_005"),  # this week
    ("asg_006", "op_002", "job_006"),  # this week
    ("asg_007", "op_005", "job_007"),  # this month
    ("asg_008", "op_003", "job_008"),  # this month
]


def _work_history(now: datetime, today: date) -> list[tuple[str, datetime, datetime]]:
    """(operator_id, start_utc, end_utc) of past work, shaped to the demo cast."""
    out: list[tuple[str, datetime, datetime]] = []

    def day_shift(op: str, days_ago: int, hours: float) -> None:
        start = shift_start(today - timedelta(days=days_ago), "day")
        out.append((op, start, start + timedelta(hours=hours)))

    # Ravi: 5 × 7.5 h on previous days + 3.5 h today ending 1 h ago → ~41 h, ok.
    for d, h in [(1, 7.5), (2, 7.5), (3, 7.5), (5, 7.5), (6, 7.5)]:
        day_shift("op_001", d, h)
    out.append(("op_001", now - timedelta(hours=4.5), now - timedelta(hours=1)))

    # Priya: 6 long days → 52 h in 7 days, warning.
    for d, h in [(1, 8.5), (2, 9.0), (3, 9.0), (4, 8.5), (5, 8.5), (6, 8.5)]:
        day_shift("op_002", d, h)

    # Arjun: light week, 20 h.
    for d, h in [(2, 6.0), (4, 7.0), (6, 7.0)]:
        day_shift("op_003", d, h)

    # Mohit: 3 earlier nights + a 12 h shift that ended 4 h ago → must_rest.
    # Earlier nights start 3+ days back so they never overlap the latest shift,
    # whatever time of day the seed runs.
    for d in (3, 4, 5):
        start = shift_start(today - timedelta(days=d), "night")
        out.append(("op_004", start, start + timedelta(hours=12)))
    out.append(("op_004", now - timedelta(hours=16), now - timedelta(hours=4)))

    # Sam: 4 × 7.5 h = 30 h.
    for d in (1, 2, 4, 5):
        day_shift("op_005", d, 7.5)

    return out


def _job_logs(rng: random.Random, today: date) -> list[JobLog]:
    logs = []
    for _ in range(60):
        op_id, _name, _lang, exp_map = rng.choice(OPERATORS)
        machine_type = rng.choice(list(MACHINE_BY_TYPE))
        experience = exp_map.get(machine_type, "novice")
        weather = rng.choices(list(WEATHER_WEIGHTS), weights=list(WEATHER_WEIGHTS.values()))[0]
        planned = rng.choice([4.0, 5.0, 5.5, 6.0, 6.5, 7.0, 8.0, 9.0, 10.0])
        ratio = (
            1.0
            + WEATHER_EFFECT[weather]
            + EXPERIENCE_EFFECT[experience]
            + MACHINE_EFFECT[machine_type]
            + rng.gauss(0, 0.05)
        )
        logs.append(
            JobLog(
                operator_id=op_id,
                machine_type=machine_type,
                operator_experience=experience,
                weather=weather,
                planned_hours=planned,
                actual_hours=round(max(0.5, planned * ratio), 2),
                date=today - timedelta(days=rng.randint(8, 120)),
            )
        )
    return logs


def seed(db_engine=engine, now: datetime | None = None, rng_seed: int = 42) -> None:
    """Drop every table, recreate, and fill with the demo data."""
    now_aware = now or datetime.now(timezone.utc)
    today = now_aware.astimezone(IST).date()
    now_utc = to_utc(now_aware)
    rng = random.Random(rng_seed)

    from app import models  # noqa: F401  (register tables)

    SQLModel.metadata.drop_all(db_engine)
    SQLModel.metadata.create_all(db_engine)

    with Session(db_engine) as db:
        for op_id, name, lang, exp in OPERATORS:
            db.add(Operator(id=op_id, name=name, lang=lang, pin=DEMO_PINS[op_id], experience=exp))

        for mc_id, mtype, model, serial, hours in MACHINES:
            db.add(Machine(
                id=mc_id, type=mtype, model=model, serial=serial, hour_meter=hours,
                status="available",
                last_inspection=shift_start(today, "day") - timedelta(hours=1, minutes=20),
            ))

        for prj_id, name, site, target_days in PROJECTS:
            db.add(Project(id=prj_id, name=name, site=site, target_date=today + timedelta(days=target_days)))

        jobs_by_id = {}
        for (job_id, prj_id, title, site, mtype, day_off, shift,
             planned, weather, hazards) in JOBS:
            job = Job(
                id=job_id, project_id=prj_id, title=title, site=site, machine_type=mtype,
                scheduled_start=shift_start(today + timedelta(days=day_off), shift),
                planned_hours=planned, status="scheduled", weather=weather, hazards=hazards,
            )
            jobs_by_id[job_id] = (job, day_off, shift)
            db.add(job)

        for asg_id, op_id, job_id in ASSIGNMENTS:
            job, day_off, shift = jobs_by_id[job_id]
            db.add(Assignment(
                id=asg_id, operator_id=op_id, job_id=job_id,
                machine_id=MACHINE_BY_TYPE[job.machine_type],
                date=today + timedelta(days=day_off), shift=shift,
            ))

        primary_machine = {op_id: MACHINE_BY_TYPE[next(iter(exp))] for op_id, _, _, exp in OPERATORS}
        for i, (op_id, start, end) in enumerate(_work_history(now_utc, today), start=1):
            db.add(WorkSession(
                id=f"ses_h{i:03d}", operator_id=op_id, machine_id=primary_machine[op_id],
                job_id="job_001",  # history only; the job link isn't used for fatigue
                state="ended", created_at=start, started_at=start, ended_at=end,
            ))

        for log in _job_logs(rng, today):
            db.add(log)

        db.commit()


if __name__ == "__main__":
    seed()
    with Session(engine) as db:
        from sqlmodel import func, select

        counts = {
            m.__name__: db.exec(select(func.count()).select_from(m)).one()
            for m in (Operator, Machine, Project, Job, Assignment, WorkSession, JobLog)
        }
    print("Seeded:", ", ".join(f"{k}={v}" for k, v in counts.items()))
    print("Demo login: op_001 Ravi Kumar, PIN 1234")
