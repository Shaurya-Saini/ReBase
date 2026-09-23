"""E6 machines. Stubbed (B0) — real in B2."""

from fastapi import APIRouter

from app import stub_data
from app.schemas import Machine

router = APIRouter(tags=["machines"])


@router.get("/machines", response_model=list[Machine])
def list_machines():
    # TODO B2
    return [stub_data.MACHINE]


@router.get("/machines/{machine_id}", response_model=Machine)
def get_machine(machine_id: str):
    # TODO B2
    return {**stub_data.MACHINE, "id": machine_id}
