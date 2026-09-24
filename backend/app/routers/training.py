"""Training Hub: E26 next module, E27 complete, and (v2.3) E28 plan, E29 module, E30 submit."""

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app import models
from app.clock import now_utc
from app.db import get_db
from app.errors import ApiError
from app.i18n import display_lang
from app.schemas import (MachineType, Ok, QuizResult, QuizSubmit, TrainingCompleteRequest, TrainingModule,
                         TrainingPlan)
from app.services import training
from app.views import get_or_404

router = APIRouter(tags=["training"])


def _module_or_404(module_id: str) -> dict:
    m = training.all_modules().get(module_id)
    if m is None:
        raise ApiError(404, "TRAINING_NOT_FOUND", f"No training module '{module_id}'")
    return m


def _record(db: Session, operator_id: str, module_id: str, score: int) -> None:
    db.add(models.TrainingCompletion(operator_id=operator_id, module_id=module_id, score=score,
                                     completed_at=now_utc()))
    db.commit()


@router.get("/operators/{operator_id}/training/next", response_model=TrainingModule)
def next_module(operator_id: str, machine_type: MachineType = MachineType.excavator,
                db: Session = Depends(get_db), lang: str = Depends(display_lang)):
    op = get_or_404(db, models.Operator, operator_id)
    m = training.next_module(op.experience, machine_type.value)
    if m is None:
        raise ApiError(404, "TRAINING_NOT_FOUND", f"No training module for {machine_type.value}")
    return training.localized(m, lang)


@router.post("/training/{module_id}/complete", response_model=Ok)
def complete_module(module_id: str, body: TrainingCompleteRequest, db: Session = Depends(get_db)):
    """`score` = number of correct quiz answers (0 … number of questions)."""
    m = _module_or_404(module_id)
    get_or_404(db, models.Operator, body.operator_id)
    if not 0 <= body.score <= len(m["quiz"]):
        raise ApiError(422, "SCORE_OUT_OF_RANGE",
                       f"score is the number of correct answers: 0 to {len(m['quiz'])}")
    _record(db, body.operator_id, module_id, int(body.score))
    return {"ok": True}


@router.get("/operators/{operator_id}/training/plan", response_model=TrainingPlan)
def training_plan(operator_id: str, db: Session = Depends(get_db), lang: str = Depends(display_lang)):
    """E28: today's personalized recap — ranked modules, each with the reasons why."""
    return training.build_plan(db, get_or_404(db, models.Operator, operator_id), lang)


@router.get("/training/modules/{module_id}", response_model=TrainingModule)
def get_module(module_id: str, lang: str = Depends(display_lang)):
    """E29: one module (e.g. from the plan) in the display language. No answers/explanations."""
    return training.localized(_module_or_404(module_id), lang)


@router.post("/training/{module_id}/submit", response_model=QuizResult)
def submit_quiz(module_id: str, body: QuizSubmit, db: Session = Depends(get_db),
                lang: str = Depends(display_lang)):
    """E30: grade the answers, record the result, return per-question feedback + manual source."""
    m = _module_or_404(module_id)
    get_or_404(db, models.Operator, body.operator_id)
    if len(body.answers) != len(m["quiz"]):
        raise ApiError(422, "ANSWER_COUNT_MISMATCH",
                       f"Expected {len(m['quiz'])} answers, got {len(body.answers)}")
    for a, q in zip(body.answers, m["quiz"]):
        if a is not None and not 0 <= a < len(q["options"]):
            raise ApiError(422, "ANSWER_OUT_OF_RANGE", f"Answer {a} is not an option of {q['q']!r}")
    result = training.grade(training.localized(m, lang), body.answers)
    _record(db, body.operator_id, module_id, result["score"])
    return result
