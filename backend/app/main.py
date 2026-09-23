"""ReBase backend. Run: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai import router_assistant, router_voice
from app.config import settings
from app.db import create_db, engine
from app.errors import install_error_handlers
from app.routers import (
    alerts,
    assignments,
    checklist,
    jobs,
    machines,
    operators,
    sessions,
    sim,
    training,
    ws,
)
from app.schemas import Health
from app.simulator.engine import engine as simulator


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db()
    _seed_if_empty()
    _train_estimator_if_missing()
    _restore_simulator()
    sim_task = asyncio.create_task(simulator.run())
    if settings.RAG_WARMUP:
        from app.ai import rag

        rag.warm_in_background()  # loads the embedding model + builds/opens the Chroma store
    yield
    sim_task.cancel()


def _seed_if_empty() -> None:
    """Fresh clone convenience: an empty DB gets the demo data automatically."""
    from sqlmodel import Session, select

    from app.models import Operator
    from app.seed import seed

    with Session(engine) as db:
        if db.exec(select(Operator)).first() is None:
            seed(engine)


def _restore_simulator() -> None:
    """Resume telemetry for sessions that were active when the server stopped."""
    from sqlmodel import Session, select

    from app.models import Machine, WorkSession

    simulator.reset()
    with Session(engine) as db:
        for s in db.exec(select(WorkSession).where(WorkSession.state == "active")).all():
            machine = db.get(Machine, s.machine_id)
            simulator.start(s.id, machine.type if machine else "excavator")


def _train_estimator_if_missing() -> None:
    """Fresh clone convenience: train the XGBoost estimator (< 1 s) if absent.
    On any failure E8 just uses its formula fallback."""
    from pathlib import Path

    if Path(settings.ESTIMATOR_PATH).exists():
        return
    try:
        from app.ai.train_estimator import train

        train(engine, verbose=False)
    except Exception as e:  # noqa: BLE001
        print(f"[startup] estimator training skipped ({e}); E8 uses the fallback formula")


app = FastAPI(title="ReBase API", version=settings.VERSION, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)
install_error_handlers(app)


@app.get("/health", response_model=Health, tags=["health"])
def health():
    return {"status": "ok", "version": settings.VERSION}


for module in (
    operators,
    machines,
    jobs,
    assignments,
    sessions,
    checklist,
    alerts,
    sim,
    ws,
    training,
    router_assistant,
    router_voice,
):
    app.include_router(module.router)
