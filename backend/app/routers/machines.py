"""E6 machines."""

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app import models
from app.db import get_db
from app.schemas import Machine
from app.i18n import display_lang
from app.views import get_or_404, machine_out

router = APIRouter(tags=["machines"])


@router.get("/machines", response_model=list[Machine])
def list_machines(db: Session = Depends(get_db), lang: str = Depends(display_lang)):
    return [machine_out(m, lang) for m in db.exec(select(models.Machine).order_by(models.Machine.id)).all()]


@router.get("/machines/{machine_id}", response_model=Machine)
def get_machine(machine_id: str, db: Session = Depends(get_db), lang: str = Depends(display_lang)):
    return machine_out(get_or_404(db, models.Machine, machine_id), lang)
