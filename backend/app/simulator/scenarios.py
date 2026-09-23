"""SimEvent → telemetry changes (E22). No alerts here — the tablet decides those.

Each nudge lasts SCENARIO_TICKS simulated seconds, then the machine returns to
normal. Targets are just past the tablet's rule thresholds
(app/lib/edge/telemetry_rules.dart); values that have a warning and a critical
level ramp over RAMP_TICKS so the tablet shows the escalation.
"""

SCENARIO_TICKS = 15
RAMP_TICKS = 4

TELEMETRY_EVENTS = {"seatbelt_off", "proximity", "excessive_idle", "overheat", "overload", "unsafe_operation"}
CAMERA_EVENTS = {"drowsiness", "distraction", "operator_absent"}  # real camera on the tablet; no-op here

IDLE_START_S = 170  # tablet threshold is 180 s → crosses ~10 s into the nudge


def _ramp(start: float, target: float, k: int) -> float:
    return start + (target - start) * min(1.0, k / RAMP_TICKS)


def overlay(event: str, k: int, d: dict) -> dict:
    """Apply scenario `event` at tick k (1-based) of the nudge to telemetry dict `d`."""
    d = dict(d)
    if event == "seatbelt_off":
        d["seatbelt"] = False
    elif event == "proximity":
        d["proximity_m"] = round(_ramp(9.0, 1.5, k), 1)  # warning <5 m, critical <2 m
    elif event == "excessive_idle":
        d.update(engine_rpm=800, load_pct=0, speed_kmh=0.0)
    elif event == "overheat":
        d["hydraulic_temp_c"] = round(_ramp(88.0, 108.0, k), 1)  # warning >95, critical >105
    elif event == "overload":
        d["load_pct"] = round(_ramp(85.0, 104.0, k))  # warning >90, critical >100
    elif event == "unsafe_operation":
        d.update(speed_kmh=18.0, load_pct=85)  # >15 km/h under >80 % load
    return d
