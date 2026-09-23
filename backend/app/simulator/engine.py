"""Telemetry simulator (W1, E22): one MachineSim per active session, 1 tick =
1 simulated second, broadcast to WebSocket subscribers every SIM_TICK_SECONDS.

- `MachineSim` is pure and deterministic given its RNG — unit-testable.
- `SimulatorEngine` owns the sims + subscriber queues and runs the async loop
  (started in main.py's lifespan). All queue work happens on the event loop;
  start/stop/nudge may be called from FastAPI's worker threads (guarded by a lock).
"""

import asyncio
import math
import random
import threading
from datetime import datetime, timezone

from app.config import settings
from app.simulator import scenarios

END = object()  # queue sentinel: session no longer active

# Normal operating profile per machine type.
PROFILES = {
    # digging cycle ~20 s; tracks a few metres every 90 s
    "excavator": {"rpm": 1850, "cycle": 20},
    # load-and-carry cycle ~30 s
    "wheel_loader": {"rpm": 1900, "cycle": 30},
    # steady drilling
    "drill_rig": {"rpm": 2000, "cycle": 40},
    # haul loaded / return empty, ~120 s cycle
    "dump_truck": {"rpm": 1700, "cycle": 120},
}


class MachineSim:
    def __init__(self, machine_type: str, rng: random.Random | None = None):
        self.machine_type = machine_type if machine_type in PROFILES else "excavator"
        self.rng = rng or random.Random()
        self.t = 0
        self.fuel = self.rng.uniform(60, 90)
        self.temp = 60.0
        self.proximity = self.rng.uniform(12, 20)
        self.idle_run = 0  # consecutive idle seconds (reported as idle_seconds)
        self.idle_total = 0  # all idle seconds this session (session summary)
        self.event: str | None = None
        self.event_tick = 0

    def nudge(self, event: str) -> None:
        if event == "normal":
            self.event, self.event_tick = None, 0
        elif event in scenarios.TELEMETRY_EVENTS:
            self.event, self.event_tick = event, 0
            if event == "excessive_idle":
                self.idle_run = max(self.idle_run, scenarios.IDLE_START_S)

    def _base(self) -> tuple[float, float, float]:
        """(rpm, load_pct, speed_kmh) for normal work at time t."""
        p, t, n = PROFILES[self.machine_type], self.t, self.rng.gauss
        phase = (t % p["cycle"]) / p["cycle"]
        rpm = p["rpm"] + n(0, 40)
        if self.machine_type == "excavator":
            load = 45 + 35 * math.sin(2 * math.pi * phase) + n(0, 3)
            speed = 2.0 if (t % 90) < 8 else 0.0
        elif self.machine_type == "wheel_loader":
            loaded = phase < 0.5
            load = (70 if loaded else 15) + n(0, 4)
            speed = (6 if loaded else 9) + n(0, 0.5)
        elif self.machine_type == "drill_rig":
            load, speed = 60 + n(0, 5), 0.0
        else:  # dump_truck
            loaded = phase < 0.5
            load = (82 if loaded else 0) + (n(0, 2) if loaded else 0)
            speed = (12 if loaded else 25) + n(0, 1)
        return rpm, max(0.0, load), max(0.0, speed)

    def step(self) -> dict:
        """Advance one simulated second; return the §5 telemetry `data` dict."""
        self.t += 1
        rpm, load, speed = self._base()
        self.fuel = max(5.0, self.fuel - 0.004)
        self.temp += (60 + 0.08 * load - self.temp) * 0.2 + self.rng.gauss(0, 0.2)
        self.proximity = min(30.0, max(8.0, self.proximity + self.rng.gauss(0, 0.6)))
        data = {
            "engine_rpm": int(rpm),
            "hydraulic_temp_c": round(self.temp, 1),
            "fuel_pct": int(self.fuel),
            "load_pct": int(round(load)),
            "speed_kmh": round(speed, 1),
            "idle_seconds": 0,
            "seatbelt": True,
            "proximity_m": round(self.proximity, 1),
        }
        if self.event:
            self.event_tick += 1
            data = scenarios.overlay(self.event, self.event_tick, data)
            if self.event == "overheat":
                self.temp = data["hydraulic_temp_c"]  # cools back down naturally afterwards
            if self.event_tick >= scenarios.SCENARIO_TICKS:
                self.event, self.event_tick = None, 0

        idle = data["speed_kmh"] == 0 and data["load_pct"] < 5
        self.idle_run = self.idle_run + 1 if idle else 0
        self.idle_total += idle
        data["idle_seconds"] = self.idle_run
        return data


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class SimulatorEngine:
    def __init__(self):
        self._lock = threading.Lock()
        self.sims: dict[str, MachineSim] = {}
        self.subs: dict[str, set[asyncio.Queue]] = {}
        self.latest: dict[str, dict] = {}

    # --- control (any thread) ---
    def reset(self) -> None:
        with self._lock:
            self.sims.clear()
            self.latest.clear()

    def start(self, session_id: str, machine_type: str, rng: random.Random | None = None) -> None:
        with self._lock:
            self.sims.setdefault(session_id, MachineSim(machine_type, rng))

    def stop(self, session_id: str) -> dict:
        """Stop a session's sim; returns {"idle_seconds": total} for the summary."""
        with self._lock:
            sim = self.sims.pop(session_id, None)
            self.latest.pop(session_id, None)
        return {"idle_seconds": sim.idle_total if sim else 0}

    def is_running(self, session_id: str) -> bool:
        return session_id in self.sims

    def nudge(self, session_id: str, event: str) -> bool:
        with self._lock:
            sim = self.sims.get(session_id)
            if sim is None:
                return False
            sim.nudge(event)
            return True

    # --- event loop side ---
    def subscribe(self, session_id: str) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue(maxsize=5)
        self.subs.setdefault(session_id, set()).add(q)
        if session_id in self.latest:
            q.put_nowait(self.latest[session_id])  # instant first frame
        return q

    def unsubscribe(self, session_id: str, q: asyncio.Queue) -> None:
        self.subs.get(session_id, set()).discard(q)

    @staticmethod
    def _offer(q: asyncio.Queue, item) -> None:
        if q.full():  # slow client: drop the oldest frame, keep the stream live
            q.get_nowait()
        q.put_nowait(item)

    def tick(self) -> None:
        with self._lock:
            frames = {sid: {"type": "telemetry", "ts": _now_iso(), "data": sim.step()}
                      for sid, sim in self.sims.items()}
            self.latest.update(frames)
        for sid, queues in list(self.subs.items()):
            for q in list(queues):
                self._offer(q, frames.get(sid, END))

    async def run(self) -> None:
        while True:
            self.tick()
            await asyncio.sleep(settings.SIM_TICK_SECONDS)


engine = SimulatorEngine()
