"""W1 /ws/sessions/{id}: server→client simulated telemetry while the session is active.

If the session doesn't exist or isn't active: send
{"type": "error", "code": "SESSION_NOT_ACTIVE"} and close (CONTRACT §5).
When the session ends (E17) connected clients get the same error and are closed.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlmodel import Session

from app import models
from app.db import engine as db_engine
from app.simulator.engine import END, engine as sim

router = APIRouter(tags=["ws"])

NOT_ACTIVE = {"type": "error", "code": "SESSION_NOT_ACTIVE"}


@router.websocket("/ws/sessions/{session_id}")
async def telemetry_ws(ws: WebSocket, session_id: str):
    await ws.accept()
    with Session(db_engine) as db:
        s = db.get(models.WorkSession, session_id)
        machine = db.get(models.Machine, s.machine_id) if s else None
    if s is None or s.state != "active":
        await ws.send_json(NOT_ACTIVE)
        await ws.close(code=1008)
        return
    sim.start(session_id, machine.type if machine else "excavator")  # no-op if already running

    q = sim.subscribe(session_id)
    try:
        while True:
            frame = await q.get()
            if frame is END:
                await ws.send_json(NOT_ACTIVE)
                await ws.close(code=1000)
                return
            await ws.send_json(frame)
    except WebSocketDisconnect:
        pass
    finally:
        sim.unsubscribe(session_id, q)
