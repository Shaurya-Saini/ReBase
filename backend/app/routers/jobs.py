"""E7 job, E8 estimate (XGBoost, formula fallback)."""

from datetime import timedelta

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app import models
from app.ai.estimator import Prediction, get_estimator
from app.clock import IST
from app.db import get_db
from app.schemas import Estimate, Job
from app.views import get_or_404

router = APIRouter(tags=["jobs"])


def _experience_for(db: Session, job: models.Job) -> str:
    """Experience of the operator assigned to this job (intermediate if unassigned)."""
    a = db.exec(
        select(models.Assignment).where(models.Assignment.job_id == job.id).order_by(models.Assignment.date)
    ).first()
    op = db.get(models.Operator, a.operator_id) if a else None
    return (op.experience.get(job.machine_type) if op else None) or "intermediate"


def predict_job(db: Session, job: models.Job) -> Prediction:
    return get_estimator().predict(job.planned_hours, job.machine_type, job.weather, _experience_for(db, job))


@router.get("/jobs/{job_id}", response_model=Job)
def get_job(job_id: str, db: Session = Depends(get_db)):
    return get_or_404(db, models.Job, job_id)


@router.get("/jobs/{job_id}/estimate", response_model=Estimate)
def get_estimate(job_id: str, db: Session = Depends(get_db)):
    job = get_or_404(db, models.Job, job_id)
    p = predict_job(db, job)

    # Project completion = latest estimated finish of the project's open jobs.
    open_jobs = db.exec(
        select(models.Job).where(models.Job.project_id == job.project_id, models.Job.status != "done")
    ).all()
    finishes = [
        j.scheduled_start + timedelta(hours=(p if j.id == job.id else predict_job(db, j)).estimated_hours)
        for j in open_jobs
    ]
    completion = max(finishes).astimezone(IST).date() if finishes else None

    return Estimate(
        job_id=job.id,
        estimated_hours=p.estimated_hours,
        range_hours=p.range_hours,
        factors=[{"name": f.name, "effect_pct": f.effect_pct, "note": f.note} for f in p.factors],
        project_completion_date=completion,
    )
