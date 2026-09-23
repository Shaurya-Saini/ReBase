"""E6 machines."""

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app import models
from app.db import get_db
from app.schemas import Machine
from app.views import get_or_404

router = APIRouter(tags=["machines"])


@router.get("/machines", response_model=list[Machine])
def list_machines(db: Session = Depends(get_db)):
    return db.exec(select(models.Machine).order_by(models.Machine.id)).all()


@router.get("/machines/{machine_id}", response_model=Machine)
def get_machine(machine_id: str, db: Session = Depends(get_db)):
    return get_or_404(db, models.Machine, machine_id)
