"""E5 operator assignments, E9 create assignment (manager, Swagger only)."""

from datetime import timedelta
from typing import Literal

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app import models
from app.clock import today_ist
from app.db import get_db
from app.errors import ApiError
from app.ids import next_id
from app.schemas import Assignment, AssignmentCreate
from app.views import assignment_out, get_or_404

router = APIRouter(tags=["assignments"])

# Upcoming window from today (IST), inclusive of today.
RANGE_DAYS = {"day": 1, "week": 7, "month": 30}


@router.get("/operators/{operator_id}/assignments", response_model=list[Assignment])
def list_assignments(
    operator_id: str,
    range: Literal["day", "week", "month"] = "day",
    db: Session = Depends(get_db),
):
    get_or_404(db, models.Operator, operator_id)
    start = today_ist()
    end = start + timedelta(days=RANGE_DAYS[range])
    rows = db.exec(
        select(models.Assignment)
        .where(models.Assignment.operator_id == operator_id)
        .where(models.Assignment.date >= start, models.Assignment.date < end)
        .order_by(models.Assignment.date, models.Assignment.shift)  # "day" < "night"
    ).all()
    return [assignment_out(db, a) for a in rows]


@router.post("/assignments", response_model=Assignment, status_code=201)
def create_assignment(body: AssignmentCreate, db: Session = Depends(get_db)):
    get_or_404(db, models.Operator, body.operator_id)
    job = get_or_404(db, models.Job, body.job_id)
    machine = get_or_404(db, models.Machine, body.machine_id)
    if machine.type != job.machine_type:
        raise ApiError(
            422, "MACHINE_TYPE_MISMATCH",
            f"Job {job.id} needs a {job.machine_type}, machine {machine.id} is a {machine.type}",
        )
    clash = db.exec(
        select(models.Assignment).where(
            models.Assignment.date == body.date,
            models.Assignment.shift == body.shift,
            (models.Assignment.operator_id == body.operator_id)
            | (models.Assignment.machine_id == body.machine_id),
        )
    ).first()
    if clash:
        raise ApiError(
            409, "ASSIGNMENT_CONFLICT",
            f"Operator or machine already assigned for {body.date} {body.shift.value} shift ({clash.id})",
        )
    a = models.Assignment(
        id=next_id(db, models.Assignment, "asg"),
        operator_id=body.operator_id,
        job_id=body.job_id,
        machine_id=body.machine_id,
        date=body.date,
        shift=body.shift.value,
    )
    db.add(a)
    db.commit()
    db.refresh(a)
    return assignment_out(db, a)
