"""ReBase backend. Run: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.ai import router_assistant, router_voice
from app.config import settings
from app.db import create_db
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


@asynccontextmanager
async def lifespan(_: FastAPI):
    create_db()
    # TODO B8: start simulator · TODO B10: warm RAG store
    yield


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
