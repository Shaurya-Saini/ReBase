"""E12 get checklist, E13 update item, E14 complete (defect gate). Logic in services/sessions.py."""

from fastapi import APIRouter, Depends
from sqlmodel import Session as DbSession

from app import models
from app.db import get_db
from app.i18n import display_lang
from app.schemas import Checklist, ChecklistItem, ChecklistItemUpdate, Session
from app.services import sessions as svc
from app.views import get_or_404

router = APIRouter(tags=["checklist"])


@router.get("/sessions/{session_id}/checklist", response_model=Checklist)
def get_checklist(session_id: str, db: DbSession = Depends(get_db), lang: str = Depends(display_lang)):
    return svc.checklist(db, get_or_404(db, models.WorkSession, session_id), lang)


@router.put("/sessions/{session_id}/checklist/items/{item_id}", response_model=ChecklistItem)
def update_item(session_id: str, item_id: str, body: ChecklistItemUpdate, db: DbSession = Depends(get_db),
                lang: str = Depends(display_lang)):
    s = get_or_404(db, models.WorkSession, session_id)
    return svc.update_item(db, s, item_id, body.status.value, body.note, lang)


@router.post("/sessions/{session_id}/checklist/complete", response_model=Session)
def complete_checklist(session_id: str, db: DbSession = Depends(get_db)):
    return svc.complete_checklist(db, get_or_404(db, models.WorkSession, session_id))
