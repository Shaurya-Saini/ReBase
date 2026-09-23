"""Job-time estimates for a job (E8, briefing)."""

from datetime import date, timedelta

from sqlmodel import Session, select

from app import models
from app.ai.estimator import Prediction, get_estimator
from app.clock import IST


def assigned_experience(db: Session, job: models.Job) -> str:
    """Experience of the operator assigned to this job (intermediate if unassigned)."""
    a = db.exec(
        select(models.Assignment).where(models.Assignment.job_id == job.id).order_by(models.Assignment.date)
    ).first()
    op = db.get(models.Operator, a.operator_id) if a else None
    return (op.experience.get(job.machine_type) if op else None) or "intermediate"


def predict_job(db: Session, job: models.Job, experience: str | None = None) -> Prediction:
    exp = experience or assigned_experience(db, job)
    return get_estimator().predict(job.planned_hours, job.machine_type, job.weather, exp)


def project_completion(db: Session, job: models.Job, this_job: Prediction) -> date | None:
    """Latest estimated finish of the project's open jobs (IST date)."""
    open_jobs = db.exec(
        select(models.Job).where(models.Job.project_id == job.project_id, models.Job.status != "done")
    ).all()
    finishes = [
        j.scheduled_start + timedelta(hours=(this_job if j.id == job.id else predict_job(db, j)).estimated_hours)
        for j in open_jobs
    ]
    return max(finishes).astimezone(IST).date() if finishes else None
