"""E23 /assistant/ask — manual Q&A (RAG + LLM). Logic in ai/assistant.py."""

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app import models
from app.ai import assistant
from app.db import get_db
from app.errors import ApiError
from app.schemas import AssistantAnswer, AssistantRequest
from app.views import get_or_404

router = APIRouter(tags=["assistant"])


@router.post("/assistant/ask", response_model=AssistantAnswer)
def ask(body: AssistantRequest, db: Session = Depends(get_db)):
    machine = get_or_404(db, models.Machine, body.machine_id)
    if body.session_id:
        get_or_404(db, models.WorkSession, body.session_id)
    question = body.question.strip()
    if not question:
        raise ApiError(422, "EMPTY_QUESTION", "Question is empty")
    return assistant.ask(question, machine.type, body.lang.value)
