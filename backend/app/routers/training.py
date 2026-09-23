"""E26 next training module, E27 complete (records the quiz result)."""

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app import models
from app.clock import now_utc
from app.db import get_db
from app.errors import ApiError
from app.schemas import MachineType, Ok, TrainingCompleteRequest, TrainingModule
from app.services import training
from app.views import get_or_404

router = APIRouter(tags=["training"])


@router.get("/operators/{operator_id}/training/next", response_model=TrainingModule)
def next_module(operator_id: str, machine_type: MachineType = MachineType.excavator,
                db: Session = Depends(get_db)):
    op = get_or_404(db, models.Operator, operator_id)
    m = training.next_module(op.experience, machine_type.value)
    if m is None:
        raise ApiError(404, "TRAINING_NOT_FOUND", f"No training module for {machine_type.value}")
    return m


@router.post("/training/{module_id}/complete", response_model=Ok)
def complete_module(module_id: str, body: TrainingCompleteRequest, db: Session = Depends(get_db)):
    """`score` = number of correct quiz answers (0 … number of questions)."""
    m = training.all_modules().get(module_id)
    if m is None:
        raise ApiError(404, "TRAINING_NOT_FOUND", f"No training module '{module_id}'")
    get_or_404(db, models.Operator, body.operator_id)
    if not 0 <= body.score <= len(m["quiz"]):
        raise ApiError(422, "SCORE_OUT_OF_RANGE",
                       f"score is the number of correct answers: 0 to {len(m['quiz'])}")
    db.add(models.TrainingCompletion(operator_id=body.operator_id, module_id=module_id,
                                     score=body.score, completed_at=now_utc()))
    db.commit()
    return {"ok": True}
