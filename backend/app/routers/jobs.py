"""E7 job, E8 estimate (estimate still stubbed — real in B6)."""

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app import models, stub_data
from app.db import get_db
from app.schemas import Estimate, Job
from app.views import get_or_404

router = APIRouter(tags=["jobs"])


@router.get("/jobs/{job_id}", response_model=Job)
def get_job(job_id: str, db: Session = Depends(get_db)):
    return get_or_404(db, models.Job, job_id)


@router.get("/jobs/{job_id}/estimate", response_model=Estimate)
def get_estimate(job_id: str, db: Session = Depends(get_db)):
    get_or_404(db, models.Job, job_id)
    # TODO B6: app.ai.estimator (XGBoost + fallback formula)
    return {**stub_data.ESTIMATE, "job_id": job_id}
