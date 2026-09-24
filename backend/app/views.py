"""DB rows → CONTRACT §4 response shapes, plus 404 lookups. Shared by routers."""

from typing import TypeVar

from sqlmodel import Session, SQLModel

from app import models, schemas
from app.i18n import DEFAULT, tr_entity
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


def operator_out(db: Session, op: models.Operator, lang: str = DEFAULT) -> schemas.Operator:
    f = operator_fatigue(db, op)
    return schemas.Operator(
        id=op.id,
        name=tr_entity(lang, "operators", op.id, "name", op.name),
        lang=op.lang,
        experience=op.experience,
        hours_today=round(f.hours_today, 1),
        hours_7d=round(f.hours_7d, 1),
        rest=f.rest,
    )


def job_out(job: models.Job, lang: str = DEFAULT) -> schemas.Job:
    out = schemas.Job.model_validate(job)
    out.title = tr_entity(lang, "jobs", job.id, "title", job.title)
    out.site = tr_entity(lang, "jobs", job.id, "site", job.site)
    return out


def machine_out(machine: models.Machine, lang: str = DEFAULT) -> schemas.Machine:
    out = schemas.Machine.model_validate(machine)
    out.model = tr_entity(lang, "machines", machine.id, "model", machine.model)
    return out


def assignment_out(db: Session, a: models.Assignment, lang: str = DEFAULT) -> schemas.Assignment:
    return schemas.Assignment(
        id=a.id,
        operator_id=a.operator_id,
        date=a.date,
        shift=a.shift,
        job=job_out(get_or_404(db, models.Job, a.job_id), lang),
        machine=machine_out(get_or_404(db, models.Machine, a.machine_id), lang),
    )
