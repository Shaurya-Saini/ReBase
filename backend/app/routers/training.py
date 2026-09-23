"""E26 next training module, E27 complete. Stubbed (B0) — real in B13."""

from fastapi import APIRouter

from app import stub_data
from app.schemas import MachineType, Ok, TrainingCompleteRequest, TrainingModule

router = APIRouter(tags=["training"])


@router.get("/operators/{operator_id}/training/next", response_model=TrainingModule)
def next_module(operator_id: str, machine_type: MachineType = MachineType.excavator):
    # TODO B13: pick by operator experience from data/training/*.yaml
    return {**stub_data.TRAINING_MODULE, "machine_type": machine_type}


@router.post("/training/{module_id}/complete", response_model=Ok)
def complete_module(module_id: str, body: TrainingCompleteRequest):
    # TODO B13: persist TrainingCompletion
    return {"ok": True}
