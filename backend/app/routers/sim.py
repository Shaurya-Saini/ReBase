"""E21 list scenarios, E22 nudge the telemetry stream of an active session."""

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app import models
from app.db import get_db
from app.errors import ApiError
from app.schemas import SIM_EVENTS, SimScenarioRequest
from app.simulator import scenarios
from app.simulator.engine import engine as sim
from app.views import get_or_404

router = APIRouter(tags=["sim"])


@router.get("/sim/scenarios", response_model=list[str])
def list_scenarios():
    return SIM_EVENTS


@router.post("/sim/scenario", status_code=202)
def set_scenario(body: SimScenarioRequest, db: Session = Depends(get_db)):
    if body.event not in SIM_EVENTS:
        raise ApiError(422, "UNKNOWN_EVENT", f"Unknown sim event '{body.event}'")
    s = get_or_404(db, models.WorkSession, body.session_id)
    if s.state != "active":
        raise ApiError(409, "SESSION_NOT_ACTIVE", f"Session {s.id} is '{s.state}', not active")
    if not sim.is_running(s.id):  # e.g. server restarted mid-session
        sim.start(s.id, get_or_404(db, models.Machine, s.machine_id).type)
    sim.nudge(s.id, body.event)

    if body.event in scenarios.CAMERA_EVENTS:
        note = "Camera events are detected live by the tablet's camera; telemetry unchanged"
    elif body.event == "normal":
        note = "Telemetry back to normal"
    else:
        note = f"Telemetry steered for ~{scenarios.SCENARIO_TICKS} s"
    return {"session_id": s.id, "event": body.event, "note": note}
