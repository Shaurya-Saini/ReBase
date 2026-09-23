"""DB rows → CONTRACT §4 response shapes, plus 404 lookups. Shared by routers."""

from typing import TypeVar

from sqlmodel import Session, SQLModel

from app import models, schemas
from app.errors import ApiError
from app.services.fatigue import operator_fatigue

T = TypeVar("T", bound=SQLModel)

_NOT_FOUND_CODES = {
    models.Operator: "OPERATOR_NOT_FOUND",
    models.Machine: "MACHINE_NOT_FOUND",
    models.Job: "JOB_NOT_FOUND",
    models.Assignment: "ASSIGNMENT_NOT_FOUND",
    models.WorkSession: "SESSION_NOT_FOUND",
    models.Alert: "ALERT_NOT_FOUND",
}


def get_or_404(db: Session, model: type[T], id_: str) -> T:
    row = db.get(model, id_)
    if row is None:
        code = _NOT_FOUND_CODES.get(model, "NOT_FOUND")
        raise ApiError(404, code, f"No {code.removesuffix('_NOT_FOUND').lower()} with id '{id_}'")
    return row


def operator_out(db: Session, op: models.Operator) -> schemas.Operator:
    f = operator_fatigue(db, op)
    return schemas.Operator(
        id=op.id,
        name=op.name,
        lang=op.lang,
        experience=op.experience,
        hours_today=round(f.hours_today, 1),
        hours_7d=round(f.hours_7d, 1),
        rest=f.rest,
    )


def assignment_out(db: Session, a: models.Assignment) -> schemas.Assignment:
    return schemas.Assignment(
        id=a.id,
        operator_id=a.operator_id,
        date=a.date,
        shift=a.shift,
        job=schemas.Job.model_validate(get_or_404(db, models.Job, a.job_id)),
        machine=schemas.Machine.model_validate(get_or_404(db, models.Machine, a.machine_id)),
    )
