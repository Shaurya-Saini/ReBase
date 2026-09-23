"""E10 create, E11 get, E15 briefing, E16 start, E17 end. Stubbed (B0) — real in B7."""

from fastapi import APIRouter

from app import stub_data
from app.schemas import Briefing, Lang, Session, SessionCreate, SessionSummary

router = APIRouter(tags=["sessions"])


@router.post("/sessions", response_model=Session, status_code=201)
def create_session(body: SessionCreate):
    # TODO B7 + B3: 409 REST_REQUIRED fatigue gate
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
