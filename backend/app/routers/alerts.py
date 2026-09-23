"""E18 app posts on-device alert, E19 list incident log, E20 ack. Stubbed (B0) — real in B9."""

from datetime import datetime, timezone

from fastapi import APIRouter

from app import stub_data
from app.schemas import Alert, AlertCreate

router = APIRouter(tags=["alerts"])


@router.post("/sessions/{session_id}/alerts", response_model=Alert, status_code=201)
def post_alert(session_id: str, body: AlertCreate):
    # TODO B9: persist with a fresh alr_ id
    return {
        **stub_data.ALERT,
        **body.model_dump(),
        "session_id": session_id,
        "ts": body.ts or datetime.now(timezone.utc),
        "acknowledged": False,
    }


@router.get("/sessions/{session_id}/alerts", response_model=list[Alert])
def list_alerts(session_id: str):
    # TODO B9
    return [{**stub_data.ALERT, "session_id": session_id}]


@router.post("/alerts/{alert_id}/ack", response_model=Alert)
def ack_alert(alert_id: str):
    # TODO B9
    return {**stub_data.ALERT, "id": alert_id, "acknowledged": True}
