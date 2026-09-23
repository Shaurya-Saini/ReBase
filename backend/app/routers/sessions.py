"""E10 create, E11 get, E15 briefing, E16 start, E17 end. Stubbed (B0) — real in B7."""

from fastapi import APIRouter, Depends
from sqlmodel import Session as DbSession

from app import models, stub_data
from app.db import get_db
from app.errors import ApiError
from app.schemas import Briefing, Lang, Session, SessionCreate, SessionSummary
from app.services.fatigue import operator_fatigue
from app.views import get_or_404

router = APIRouter(tags=["sessions"])


@router.post("/sessions", response_model=Session, status_code=201)
def create_session(body: SessionCreate, db: DbSession = Depends(get_db)):
    op = get_or_404(db, models.Operator, body.operator_id)
    rest = operator_fatigue(db, op).rest
    if rest["status"] == "must_rest":
        nxt = rest["next_allowed_start"]
        raise ApiError(
            409, "REST_REQUIRED", rest["reason"],
            next_allowed_start=nxt.isoformat().replace("+00:00", "Z") if nxt else None,
        )
    # TODO B7: persist the session (machine/job checks, ses_ id)
    return {**stub_data.SESSION, **body.model_dump()}


@router.get("/sessions/{session_id}", response_model=Session)
def get_session(session_id: str):
    # TODO B7
    return {**stub_data.SESSION, "id": session_id}


@router.get("/sessions/{session_id}/briefing", response_model=Briefing)
def get_briefing(session_id: str, lang: Lang = Lang.en_IN):
    # TODO B7: app.ai.briefing (LLM + template fallback)
    return {**stub_data.BRIEFING, "session_id": session_id, "lang": lang}


@router.post("/sessions/{session_id}/start", response_model=Session)
def start_session(session_id: str):
    # TODO B7: state briefing -> active, start simulator
    return {**stub_data.SESSION, "id": session_id, "state": "active",
            "started_at": "2026-09-24T03:30:00Z"}


@router.post("/sessions/{session_id}/end", response_model=SessionSummary)
def end_session(session_id: str):
    # TODO B7: state -> ended, stop simulator, compute summary
    return {**stub_data.SESSION_SUMMARY, "session_id": session_id}
