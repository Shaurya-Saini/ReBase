"""E12 get checklist, E13 update item, E14 complete (defect gate). Stubbed (B0) — real in B7/B10."""

from fastapi import APIRouter

from app import stub_data
from app.schemas import Checklist, ChecklistItem, ChecklistItemUpdate, Session

router = APIRouter(tags=["checklist"])


@router.get("/sessions/{session_id}/checklist", response_model=Checklist)
def get_checklist(session_id: str):
    # TODO B10: content from data/checklists/<machine_type>.yaml + per-session status
    return {**stub_data.CHECKLIST, "session_id": session_id}


@router.put("/sessions/{session_id}/checklist/items/{item_id}", response_model=ChecklistItem)
def update_item(session_id: str, item_id: str, body: ChecklistItemUpdate):
    # TODO B7: persist status/note
    items = [i for s in stub_data.CHECKLIST["sections"] for i in s["items"]]
    base = next((i for i in items if i["id"] == item_id), items[0])
    return {**base, "id": item_id, "status": body.status, "note": body.note}


@router.post("/sessions/{session_id}/checklist/complete", response_model=Session)
def complete_checklist(session_id: str):
    # TODO B7: 422 CHECKLIST_INCOMPLETE / CRITICAL_DEFECT (with "items") gate
    return {**stub_data.SESSION, "id": session_id, "state": "briefing"}
