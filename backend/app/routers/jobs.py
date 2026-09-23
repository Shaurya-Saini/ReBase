"""E7 job, E8 estimate (XGBoost, formula fallback)."""

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app import models
from app.db import get_db
from app.schemas import Estimate, Job
from app.services.estimates import predict_job, project_completion
from app.views import get_or_404

router = APIRouter(tags=["jobs"])


@router.get("/jobs/{job_id}", response_model=Job)
def get_job(job_id: str, db: Session = Depends(get_db)):
    return get_or_404(db, models.Job, job_id)


@router.get("/jobs/{job_id}/estimate", response_model=Estimate)
def get_estimate(job_id: str, db: Session = Depends(get_db)):
    job = get_or_404(db, models.Job, job_id)
    p = predict_job(db, job)
    return Estimate(
        job_id=job.id,
        estimated_hours=p.estimated_hours,
        range_hours=p.range_hours,
        factors=[{"name": f.name, "effect_pct": f.effect_pct, "note": f.note} for f in p.factors],
        project_completion_date=project_completion(db, job, p),
    )
