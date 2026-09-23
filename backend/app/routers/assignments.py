"""E5 operator assignments, E9 create assignment (manager, Swagger only). Stubbed (B0) — real in B2."""

from typing import Literal

from fastapi import APIRouter

from app import stub_data
from app.schemas import Assignment, AssignmentCreate

router = APIRouter(tags=["assignments"])


@router.get("/operators/{operator_id}/assignments", response_model=list[Assignment])
def list_assignments(operator_id: str, range: Literal["day", "week", "month"] = "day"):
    # TODO B2: filter by date range
    return [{**stub_data.ASSIGNMENT, "operator_id": operator_id}]


@router.post("/assignments", response_model=Assignment, status_code=201)
def create_assignment(body: AssignmentCreate):
    # TODO B2: persist
    return {
        **stub_data.ASSIGNMENT,
        "operator_id": body.operator_id,
        "date": body.date,
        "shift": body.shift,
    }
