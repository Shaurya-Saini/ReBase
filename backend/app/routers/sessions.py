"""E10 create, E11 get, E15 briefing, E16 start, E17 end. Logic in services/sessions.py."""

from fastapi import APIRouter, Depends
from sqlmodel import Session as DbSession

from app import models
from app.ai import briefing
from app.db import get_db
from app.schemas import Briefing, Lang, Session, SessionCreate, SessionSummary
from app.services import sessions as svc
from app.views import get_or_404

router = APIRouter(tags=["sessions"])


@router.post("/sessions", response_model=Session, status_code=201)
def create_session(body: SessionCreate, db: DbSession = Depends(get_db)):
    return svc.create(db, body.operator_id, body.machine_id, body.job_id)


@router.get("/sessions/{session_id}", response_model=Session)
def get_session(session_id: str, db: DbSession = Depends(get_db)):
    return get_or_404(db, models.WorkSession, session_id)


@router.get("/sessions/{session_id}/briefing", response_model=Briefing)
def get_briefing(session_id: str, lang: Lang = Lang.en_IN, db: DbSession = Depends(get_db)):
    s = get_or_404(db, models.WorkSession, session_id)
    svc._require_state(s, "briefing", "active")
    return briefing.build(db, s, lang.value)


@router.post("/sessions/{session_id}/start", response_model=Session)
def start_session(session_id: str, db: DbSession = Depends(get_db)):
    return svc.start(db, get_or_404(db, models.WorkSession, session_id))


@router.post("/sessions/{session_id}/end", response_model=SessionSummary)
def end_session(session_id: str, db: DbSession = Depends(get_db)):
    return svc.end(db, get_or_404(db, models.WorkSession, session_id))
