"""Generate a labeled telemetry dataset that mirrors the backend simulator's
distributions and the on-device rule thresholds (app/lib/edge/telemetry_rules.dart).

Each row is one telemetry tick; the label is the safety class. The edge model
learns this mapping, so it approximates the rules from data (a distillation) —
a real trained model that runs on-device.

Run:  python gen_data.py   ->   data/telemetry.csv
"""
import os

import numpy as np
import pandas as pd

RNG = np.random.default_rng(42)

LABELS = [
    "normal",
    "seatbelt_off",
    "proximity",
    "excessive_idle",
    "overheat",
    "overload",
    "unsafe_operation",
]

FEATURES = [
    "engine_rpm",
    "hydraulic_temp_c",
    "fuel_pct",
    "load_pct",
    "speed_kmh",
    "idle_seconds",
    "seatbelt",
    "proximity_m",
]


def sample(scenario: str, n: int) -> np.ndarray:
    # Baseline "normal" ranges (mirror the simulator's nominal band).
    rpm = RNG.uniform(800, 2200, n)
    temp = RNG.uniform(55, 80, n)
    fuel = RNG.uniform(40, 90, n)
    load = RNG.uniform(0, 70, n)
    speed = RNG.uniform(0, 8, n)
    idle = RNG.uniform(0, 60, n)
    belt = np.ones(n)
    prox = RNG.uniform(8, 20, n)

    if scenario == "seatbelt_off":
        belt = np.zeros(n)
        speed = RNG.uniform(1, 12, n)
    elif scenario == "proximity":
        prox = RNG.uniform(0.5, 4.8, n)
    elif scenario == "excessive_idle":
        idle = RNG.uniform(185, 600, n)
        speed = np.zeros(n)
    elif scenario == "overheat":
        temp = RNG.uniform(96, 130, n)
    elif scenario == "overload":
        load = RNG.uniform(92, 140, n)
    elif scenario == "unsafe_operation":
        speed = RNG.uniform(16, 35, n)
        load = RNG.uniform(82, 120, n)

    return np.column_stack([rpm, temp, fuel, load, speed, idle, belt, prox])


def main() -> None:
    per = {
        "normal": 4000,
        "seatbelt_off": 800,
        "proximity": 800,
        "excessive_idle": 800,
        "overheat": 800,
        "overload": 800,
        "unsafe_operation": 800,
    }

    xs, ys = [], []
    for i, lab in enumerate(LABELS):
        xs.append(sample(lab, per[lab]))
        ys += [i] * per[lab]
    x = np.vstack(xs)

    # Feature noise so classes overlap and the model has to learn, not memorize.
    noise_sd = np.array([30, 1.0, 1.0, 1.0, 0.3, 3, 0.0, 0.3])
    x = x + RNG.normal(0, noise_sd, x.shape)

    df = pd.DataFrame(x, columns=FEATURES)
    df["label"] = ys
    os.makedirs("data", exist_ok=True)
    df.to_csv("data/telemetry.csv", index=False)
    print("wrote data/telemetry.csv", df.shape)


if __name__ == "__main__":
    main()
