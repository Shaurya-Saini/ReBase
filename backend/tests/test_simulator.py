"""B8: telemetry simulator, scenarios (E21/E22) and the W1 WebSocket stream.

The thresholds mirror the tablet's rule engine (app/lib/edge/telemetry_rules.dart)
so we know each scenario really makes the on-device rule fire.
"""

import random

import pytest

from app.simulator import scenarios
from app.simulator.engine import MachineSim, SimulatorEngine

# From TelemetryThresholds in telemetry_rules.dart
OVERHEAT_WARN, OVERHEAT_CRIT = 95, 105
PROX_WARN, PROX_CRIT = 5, 2
IDLE_WARN = 180
OVERLOAD_WARN, OVERLOAD_CRIT = 90, 100
UNSAFE_SPEED, UNSAFE_LOAD = 15, 80

KEYS = {"engine_rpm", "hydraulic_temp_c", "fuel_pct", "load_pct", "speed_kmh",
        "idle_seconds", "seatbelt", "proximity_m"}
MTYPES = ["excavator", "wheel_loader", "drill_rig", "dump_truck"]


def run(sim, n):
    return [sim.step() for _ in range(n)]


def fires(d):
    """Which tablet rules would fire on this frame (same logic as the Dart engine)."""
    out = set()
    if d["seatbelt"] is False:
        out.add("seatbelt_off")
    if d["proximity_m"] < PROX_WARN:
        out.add("proximity")
    if d["idle_seconds"] > IDLE_WARN:
        out.add("excessive_idle")
    if d["hydraulic_temp_c"] > OVERHEAT_WARN:
        out.add("overheat")
    if d["load_pct"] > OVERLOAD_WARN:
        out.add("overload")
    if d["speed_kmh"] > UNSAFE_SPEED and d["load_pct"] > UNSAFE_LOAD:
        out.add("unsafe_operation")
    return out


# ---------- MachineSim ----------

@pytest.mark.parametrize("mtype", MTYPES)
def test_normal_operation_never_trips_a_rule(mtype):
    frames = run(MachineSim(mtype, random.Random(1)), 600)  # 10 simulated minutes
    for d in frames:
        assert set(d) == KEYS
        assert fires(d) == set(), (mtype, d)
    assert len({d["load_pct"] for d in frames}) > 5  # it actually moves


def test_types_and_fuel():
    frames = run(MachineSim("dump_truck", random.Random(2)), 300)
    d = frames[-1]
    assert isinstance(d["engine_rpm"], int) and isinstance(d["fuel_pct"], int)
    assert isinstance(d["load_pct"], int) and isinstance(d["idle_seconds"], int)
    assert isinstance(d["seatbelt"], bool)
    assert frames[0]["fuel_pct"] >= frames[-1]["fuel_pct"]
    assert max(f["speed_kmh"] for f in frames) > 20  # empty return leg


@pytest.mark.parametrize("event", sorted(scenarios.TELEMETRY_EVENTS))
def test_each_scenario_fires_its_rule_then_clears(event):
    sim = MachineSim("excavator", random.Random(3))
    run(sim, 30)
    sim.nudge(event)
    during = run(sim, scenarios.SCENARIO_TICKS)
    assert any(event in fires(d) for d in during), event
    after = run(sim, 25)
    assert event not in fires(after[-1])  # back to normal


def test_escalating_scenarios_pass_warning_then_critical():
    sim = MachineSim("excavator", random.Random(4))
    sim.nudge("proximity")
    prox = [d["proximity_m"] for d in run(sim, scenarios.SCENARIO_TICKS)]
    first_warn = next(i for i, p in enumerate(prox) if p < PROX_WARN)
    first_crit = next(i for i, p in enumerate(prox) if p < PROX_CRIT)
    assert first_warn < first_crit  # the tablet sees warning, then escalation

    sim.nudge("overheat")
    temps = [d["hydraulic_temp_c"] for d in run(sim, scenarios.SCENARIO_TICKS)]
    assert next(i for i, t in enumerate(temps) if t > OVERHEAT_WARN) < \
        next(i for i, t in enumerate(temps) if t > OVERHEAT_CRIT)


def test_normal_event_cancels_and_camera_events_are_noops():
    sim = MachineSim("excavator", random.Random(5))
    sim.nudge("seatbelt_off")
    assert sim.step()["seatbelt"] is False
    sim.nudge("normal")
    assert sim.step()["seatbelt"] is True
    sim.nudge("drowsiness")
    assert sim.event is None


def test_idle_tracking_for_summary():
    sim = MachineSim("drill_rig", random.Random(6))
    run(sim, 10)
    assert sim.idle_total == 0
    sim.nudge("excessive_idle")
    run(sim, scenarios.SCENARIO_TICKS)
    assert sim.idle_total == scenarios.SCENARIO_TICKS


# ---------- engine ----------

def test_engine_start_stop_nudge():
    eng = SimulatorEngine()
    assert eng.nudge("ses_x", "overheat") is False
    eng.start("ses_x", "excavator", random.Random(7))
    assert eng.is_running("ses_x") and eng.nudge("ses_x", "excessive_idle")
    for _ in range(scenarios.SCENARIO_TICKS):
        eng.tick()
    assert eng.latest["ses_x"]["type"] == "telemetry"
    assert eng.stop("ses_x") == {"idle_seconds": scenarios.SCENARIO_TICKS}
    assert not eng.is_running("ses_x")


# ---------- API + WebSocket ----------

RAVI = {"operator_id": "op_001", "machine_id": "mc_001", "job_id": "job_001"}


def active_session(client):
    sid = client.post("/sessions", json=RAVI).json()["id"]
    chk = client.get(f"/sessions/{sid}/checklist").json()
    for sec in chk["sections"]:
        for i in sec["items"]:
            client.put(f"/sessions/{sid}/checklist/items/{i['id']}", json={"status": "ok"})
    client.post(f"/sessions/{sid}/checklist/complete")
    client.post(f"/sessions/{sid}/start")
    return sid


def test_ws_rejects_inactive_session(client):
    with client.websocket_connect("/ws/sessions/ses_999") as ws:
        assert ws.receive_json() == {"type": "error", "code": "SESSION_NOT_ACTIVE"}
    sid = client.post("/sessions", json=RAVI).json()["id"]  # pre_start
    with client.websocket_connect(f"/ws/sessions/{sid}") as ws:
        assert ws.receive_json()["code"] == "SESSION_NOT_ACTIVE"


def test_ws_streams_contract_frames(client):
    sid = active_session(client)
    with client.websocket_connect(f"/ws/sessions/{sid}") as ws:
        frames = [ws.receive_json() for _ in range(3)]
    for f in frames:
        assert f["type"] == "telemetry" and f["ts"].endswith("Z") and set(f["data"]) == KEYS


def test_scenario_reaches_the_stream(client):
    sid = active_session(client)
    r = client.post("/sim/scenario", json={"session_id": sid, "event": "seatbelt_off"})
    assert r.status_code == 202 and r.json()["event"] == "seatbelt_off"
    with client.websocket_connect(f"/ws/sessions/{sid}") as ws:
        seen = [ws.receive_json()["data"]["seatbelt"] for _ in range(5)]
    assert False in seen


def test_end_closes_stream_and_reports_idle(client):
    sid = active_session(client)
    client.post("/sim/scenario", json={"session_id": sid, "event": "excessive_idle"})
    with client.websocket_connect(f"/ws/sessions/{sid}") as ws:
        for _ in range(scenarios.SCENARIO_TICKS + 2):
            ws.receive_json()
        summary = client.post(f"/sessions/{sid}/end").json()
        msg = ws.receive_json()
        while msg["type"] == "telemetry":  # frames already queued before the end
            msg = ws.receive_json()
        assert msg == {"type": "error", "code": "SESSION_NOT_ACTIVE"}
    assert summary["idle_minutes"] >= round(scenarios.SCENARIO_TICKS / 60, 1)


def test_sim_scenario_errors(client):
    assert set(client.get("/sim/scenarios").json()) >= {"normal", "seatbelt_off", "drowsiness"}
    r = client.post("/sim/scenario", json={"session_id": "ses_999", "event": "overheat"})
    assert r.status_code == 404 and r.json()["error"]["code"] == "SESSION_NOT_FOUND"
    sid = client.post("/sessions", json=RAVI).json()["id"]
    r = client.post("/sim/scenario", json={"session_id": sid, "event": "overheat"})
    assert r.status_code == 409 and r.json()["error"]["code"] == "SESSION_NOT_ACTIVE"
    r = client.post("/sim/scenario", json={"session_id": sid, "event": "nope"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "UNKNOWN_EVENT"


def test_camera_event_is_accepted_but_explained(client):
    sid = active_session(client)
    r = client.post("/sim/scenario", json={"session_id": sid, "event": "drowsiness"})
    assert r.status_code == 202 and "camera" in r.json()["note"].lower()
