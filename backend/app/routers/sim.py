"""E21 list scenarios, E22 nudge the telemetry stream. Stubbed (B0) — real in B8."""

from fastapi import APIRouter

from app.errors import ApiError
from app.schemas import SIM_EVENTS, SimScenarioRequest

router = APIRouter(tags=["sim"])


@router.get("/sim/scenarios", response_model=list[str])
def list_scenarios():
    return SIM_EVENTS


@router.post("/sim/scenario", status_code=202)
def set_scenario(body: SimScenarioRequest):
    if body.event not in SIM_EVENTS:
        raise ApiError(422, "UNKNOWN_EVENT", f"Unknown sim event '{body.event}'")
    # TODO B8: steer the simulator for body.session_id
    return {"session_id": body.session_id, "event": body.event}
