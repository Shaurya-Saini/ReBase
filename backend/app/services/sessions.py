"""Session state machine + checklist status + critical-defect gate (E10–E17).

    pre_start ──E14──▶ briefing ──E16──▶ active ──E17──▶ ended

E10 create checks, in order: operator/machine/job exist, fatigue gate
(REST_REQUIRED), machine type matches job, machine not in maintenance, machine
not in someone else's active session, operator has no active session. An
operator's unfinished pre_start/briefing sessions are abandoned (ended, never
started) so a demo can simply start over.
"""

from sqlmodel import Session, select

from app import models
from app.ai.checklists import checklist_items, load_checklist
from app.clock import now_utc
from app.errors import ApiError
from app.i18n import DEFAULT, tr
from app.ids import next_id
from app.services.fatigue import operator_fatigue
from app.simulator.engine import engine as sim
from app.views import get_or_404

NOT_STARTED = ("pre_start", "briefing")


def _require_state(s: models.WorkSession, *allowed: str) -> None:
    if s.state not in allowed:
        raise ApiError(
            409, "INVALID_STATE",
            f"Session {s.id} is '{s.state}'; this needs {' or '.join(allowed)}",
            state=s.state, expected=list(allowed),
        )


def _fatigue_gate(db: Session, op: models.Operator) -> None:
    rest = operator_fatigue(db, op).rest
    if rest["status"] == "must_rest":
        nxt = rest["next_allowed_start"]
        raise ApiError(
            409, "REST_REQUIRED", rest["reason"],
            next_allowed_start=nxt.isoformat().replace("+00:00", "Z") if nxt else None,
        )


def create(db: Session, operator_id: str, machine_id: str, job_id: str) -> models.WorkSession:
    op = get_or_404(db, models.Operator, operator_id)
    machine = get_or_404(db, models.Machine, machine_id)
    job = get_or_404(db, models.Job, job_id)
    _fatigue_gate(db, op)
    if machine.type != job.machine_type:
        raise ApiError(422, "MACHINE_TYPE_MISMATCH",
                       f"Job {job.id} needs a {job.machine_type}, machine {machine.id} is a {machine.type}")
    if machine.status == "maintenance":
        raise ApiError(409, "MACHINE_UNAVAILABLE", f"Machine {machine.id} is in maintenance")

    active = db.exec(select(models.WorkSession).where(models.WorkSession.state == "active")).all()
    for s in active:
        if s.operator_id == operator_id:
            raise ApiError(409, "SESSION_ALREADY_ACTIVE",
                           f"Operator already has an active session {s.id}; end it first", session_id=s.id)
        if s.machine_id == machine_id:
            raise ApiError(409, "MACHINE_IN_USE",
                           f"Machine {machine.id} is in use in session {s.id}", session_id=s.id)

    now = now_utc()
    for s in db.exec(select(models.WorkSession).where(
            models.WorkSession.operator_id == operator_id,
            models.WorkSession.state.in_(NOT_STARTED))).all():
        s.state, s.ended_at = "ended", now  # abandoned before starting; not counted as work

    s = models.WorkSession(id=next_id(db, models.WorkSession, "ses"), operator_id=operator_id,
                           machine_id=machine_id, job_id=job_id, state="pre_start", created_at=now)
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


# ---------- checklist ----------

def _machine_type(db: Session, s: models.WorkSession) -> str:
    return get_or_404(db, models.Machine, s.machine_id).type


def _states(db: Session, session_id: str) -> dict[str, models.ChecklistItemState]:
    rows = db.exec(select(models.ChecklistItemState)
                   .where(models.ChecklistItemState.session_id == session_id)).all()
    return {r.item_id: r for r in rows}


def checklist(db: Session, s: models.WorkSession, lang: str = DEFAULT) -> dict:
    mtype = _machine_type(db, s)
    content = load_checklist(mtype)
    states = _states(db, s.id)

    def item(i: dict) -> dict:
        st = states.get(i["id"])
        return {**i, "text": tr(lang, "checklist_items", i["text"], i["text"]),
                "status": st.status if st else "pending", "note": st.note if st else None}

    return {
        "session_id": s.id,
        "machine_type": mtype,
        "standard_refs": content["standard_refs"],
        "sections": [{"title": tr(lang, "checklist_sections", sec["title"], sec["title"]),
                      "items": [item(i) for i in sec["items"]]}
                     for sec in content["sections"]],
    }


def update_item(db: Session, s: models.WorkSession, item_id: str, status: str, note: str | None,
                lang: str = DEFAULT) -> dict:
    _require_state(s, "pre_start")
    items = checklist_items(_machine_type(db, s))
    if item_id not in items:
        raise ApiError(404, "CHECKLIST_ITEM_NOT_FOUND", f"No checklist item '{item_id}' for this machine")
    row = db.get(models.ChecklistItemState, (s.id, item_id)) or models.ChecklistItemState(
        session_id=s.id, item_id=item_id)
    row.status, row.note, row.updated_at = status, note, now_utc()
    db.add(row)
    db.commit()
    item = items[item_id]
    return {**item, "text": tr(lang, "checklist_items", item["text"], item["text"]), "status": status, "note": note}


def complete_checklist(db: Session, s: models.WorkSession) -> models.WorkSession:
    _require_state(s, "pre_start")
    machine = get_or_404(db, models.Machine, s.machine_id)
    items = checklist_items(machine.type)
    states = _states(db, s.id)
    status = {i: (states[i].status if i in states else "pending") for i in items}

    critical_defects = [i for i, st in status.items() if st == "defect" and items[i]["critical"]]
    if critical_defects:
        raise ApiError(422, "CRITICAL_DEFECT", "Critical items have defects", items=critical_defects)
    pending = [i for i, st in status.items() if st == "pending"]
    if pending:
        raise ApiError(422, "CHECKLIST_INCOMPLETE", f"{len(pending)} checklist items not checked", items=pending)

    s.state = "briefing"
    machine.last_inspection = now_utc()
    db.add_all([s, machine])
    db.commit()
    db.refresh(s)
    return s


def defects(db: Session, s: models.WorkSession) -> list[dict]:
    """Non-blocking defects recorded on the checklist (for the briefing)."""
    items = checklist_items(_machine_type(db, s))
    return [{"text": items[r.item_id]["text"], "note": r.note}
            for r in _states(db, s.id).values() if r.status == "defect" and r.item_id in items]


# ---------- start / end ----------

def start(db: Session, s: models.WorkSession) -> models.WorkSession:
    _require_state(s, "briefing")
    _fatigue_gate(db, get_or_404(db, models.Operator, s.operator_id))
    machine = get_or_404(db, models.Machine, s.machine_id)
    job = get_or_404(db, models.Job, s.job_id)
    s.state, s.started_at = "active", now_utc()
    machine.status = "in_use"
    if job.status == "scheduled":
        job.status = "in_progress"
    db.add_all([s, machine, job])
    db.commit()
    db.refresh(s)
    sim.start(s.id, machine.type)
    return s


def end(db: Session, s: models.WorkSession) -> dict:
    _require_state(s, "active")
    machine = get_or_404(db, models.Machine, s.machine_id)
    s.state, s.ended_at = "ended", now_utc()
    machine.status = "available"
    db.add_all([s, machine])
    db.commit()
    db.refresh(s)
    idle_s = sim.stop(s.id)["idle_seconds"]

    alerts = db.exec(select(models.Alert).where(models.Alert.session_id == s.id)).all()
    return {
        "session_id": s.id,
        "duration_hours": round((s.ended_at - s.started_at).total_seconds() / 3600, 2),
        "alerts_total": len(alerts),
        "alerts_critical": sum(a.severity == "critical" for a in alerts),
        "idle_minutes": round(idle_s / 60, 1),
    }
