"""Incident log: E18 app posts an on-device alert, E19 list, E20 acknowledge.

Alerts are detected on the tablet (camera CV + telemetry rules); the backend
validates, stores and serves them. The tablet posts a new alert when a hazard
escalates (warning → critical), so each is its own incident.

- E18 accepts alerts for `active` sessions, and for `ended` ones so an alert
  in flight when the session ends isn't lost. pre_start/briefing → 409.
- A retried post (same session, type, severity and ts) returns the stored
  alert instead of duplicating it.
- E19 lists newest first.
"""

from datetime import timezone

from fastapi import APIRouter, Depends, Response
from sqlmodel import Session, select

from app import models
from app.clock import now_utc
from app.db import get_db
from app.errors import ApiError
from app.ids import next_id
from app.schemas import Alert, AlertCreate
from app.views import get_or_404

router = APIRouter(tags=["alerts"])

ACCEPTS_ALERTS = ("active", "ended")


@router.post("/sessions/{session_id}/alerts", response_model=Alert, status_code=201)
def post_alert(session_id: str, body: AlertCreate, response: Response, db: Session = Depends(get_db)):
    s = get_or_404(db, models.WorkSession, session_id)
    if s.state not in ACCEPTS_ALERTS:
        raise ApiError(409, "SESSION_NOT_ACTIVE",
                       f"Session {s.id} is '{s.state}'; alerts are logged once work has started")
    ts = body.ts or now_utc()
    if ts.tzinfo is None:  # contract says UTC; treat a naive timestamp as UTC
        ts = ts.replace(tzinfo=timezone.utc)

    existing = db.exec(select(models.Alert).where(
        models.Alert.session_id == s.id, models.Alert.type == body.type.value,
        models.Alert.severity == body.severity.value, models.Alert.ts == ts)).first()
    if existing:
        response.status_code = 200
        return existing

    a = models.Alert(id=next_id(db, models.Alert, "alr"), session_id=s.id, type=body.type.value,
                     source=body.source.value, severity=body.severity.value, message=body.message,
                     ts=ts, acknowledged=False)
    db.add(a)
    db.commit()
    db.refresh(a)
    return a


@router.get("/sessions/{session_id}/alerts", response_model=list[Alert])
def list_alerts(session_id: str, db: Session = Depends(get_db)):
    get_or_404(db, models.WorkSession, session_id)
    return db.exec(select(models.Alert).where(models.Alert.session_id == session_id)
                   .order_by(models.Alert.ts.desc(), models.Alert.id.desc())).all()


@router.post("/alerts/{alert_id}/ack", response_model=Alert)
def ack_alert(alert_id: str, db: Session = Depends(get_db)):
    a = get_or_404(db, models.Alert, alert_id)
    if not a.acknowledged:  # idempotent
        a.acknowledged = True
        db.add(a)
        db.commit()
        db.refresh(a)
    return a
