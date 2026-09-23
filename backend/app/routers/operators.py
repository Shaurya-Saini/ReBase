"""E2 login, E3 list operators, E4 one operator (hours + rest). Stubbed (B0) — real in B2/B3."""

from fastapi import APIRouter

from app import stub_data
from app.schemas import LoginRequest, Operator

router = APIRouter(tags=["operators"])


@router.post("/auth/login", response_model=Operator)
def login(body: LoginRequest):
    # TODO B2: look up operator, 401 BAD_PIN on mismatch.
    return {**stub_data.OPERATOR, "id": body.operator_id}


@router.get("/operators", response_model=list[Operator])
def list_operators():
    # TODO B2
    return [stub_data.OPERATOR]


@router.get("/operators/{operator_id}", response_model=Operator)
def get_operator(operator_id: str):
    # TODO B2 + B3 (hours_today, hours_7d, rest from fatigue service)
    return {**stub_data.OPERATOR, "id": operator_id}
