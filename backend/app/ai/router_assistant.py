"""E23 /assistant/ask (RAG + LLM). Stubbed (B0) — real in B11."""

from fastapi import APIRouter

from app import stub_data
from app.schemas import AssistantAnswer, AssistantRequest

router = APIRouter(tags=["assistant"])


@router.post("/assistant/ask", response_model=AssistantAnswer)
def ask(body: AssistantRequest):
    # TODO B11: retrieve top-k manual sections -> LLM answers in body.lang
    return {**stub_data.ASSISTANT_ANSWER, "lang": body.lang}
