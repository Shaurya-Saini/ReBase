"""E7 job, E8 estimate. Stubbed (B0) — real in B2 (job) and B6 (XGBoost estimate)."""

from fastapi import APIRouter

from app import stub_data
from app.schemas import Estimate, Job

router = APIRouter(tags=["jobs"])


@router.get("/jobs/{job_id}", response_model=Job)
def get_job(job_id: str):
    # TODO B2
    return {**stub_data.JOB, "id": job_id}


@router.get("/jobs/{job_id}/estimate", response_model=Estimate)
def get_estimate(job_id: str):
    # TODO B6: app.ai.estimator (XGBoost + fallback formula)
    return {**stub_data.ESTIMATE, "job_id": job_id}
