"""W1 /ws/sessions/{id}: server→client telemetry, one tick per SIM_TICK_SECONDS.

Stubbed (B0): streams the CONTRACT §5 example for any session. B8 replaces this
with the simulator engine and the SESSION_NOT_ACTIVE check.
"""

import asyncio
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app import stub_data
from app.config import settings

router = APIRouter(tags=["ws"])


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@router.websocket("/ws/sessions/{session_id}")
async def telemetry_ws(ws: WebSocket, session_id: str):
    await ws.accept()
    try:
        while True:
            await ws.send_json(
                {"type": "telemetry", "ts": _now_iso(), "data": stub_data.TELEMETRY_DATA}
            )
            await asyncio.sleep(settings.SIM_TICK_SECONDS)
    except WebSocketDisconnect:
        pass
