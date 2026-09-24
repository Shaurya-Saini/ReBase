"""E2 login, E3 list operators, E4 one operator (hours + rest from the fatigue service)."""

from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from app import models
from app.db import get_db
from app.errors import ApiError
from app.i18n import display_lang
from app.schemas import LoginRequest, Operator
from app.views import get_or_404, operator_out

router = APIRouter(tags=["operators"])


@router.post("/auth/login", response_model=Operator)
def login(body: LoginRequest, db: Session = Depends(get_db), lang: str = Depends(display_lang)):
    op = get_or_404(db, models.Operator, body.operator_id)
    if body.pin != op.pin:
        raise ApiError(401, "BAD_PIN", "Incorrect PIN")
    return operator_out(db, op, lang)


@router.get("/operators", response_model=list[Operator])
def list_operators(db: Session = Depends(get_db), lang: str = Depends(display_lang)):
    ops = db.exec(select(models.Operator).order_by(models.Operator.id)).all()
    return [operator_out(db, op, lang) for op in ops]


@router.get("/operators/{operator_id}", response_model=Operator)
def get_operator(operator_id: str, db: Session = Depends(get_db), lang: str = Depends(display_lang)):
    return operator_out(db, get_or_404(db, models.Operator, operator_id), lang)
