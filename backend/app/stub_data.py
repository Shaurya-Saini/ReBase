"""B0 stubs: the CONTRACT.md §4 JSON examples, verbatim.

Routers return these until the real implementation (B1–B13) replaces them.
Delete entries as they stop being used.
"""


ASSISTANT_ANSWER = {
    "answer": "…(answer in hi-IN)…",
    "lang": "hi-IN",
    "sources": [{"doc": "excavator_manual.md", "section": "4.2 Operating modes"}],
}

TRAINING_MODULE = {
    "id": "trn_ex_novice_01",
    "machine_type": "excavator",
    "level": "novice",
    "title": "Excavator basics before your shift",
    "duration_min": 30,
    "steps": [
        {"kind": "text", "content": "The joystick pattern on this machine is ISO.", "url": None},
        {"kind": "video", "content": "Walk-around inspection", "url": "https://example.com/video"},
        {"kind": "tip", "content": "Never swing over the ground crew.", "url": None},
    ],
    "quiz": [
        {"q": "What must you do if a hydraulic hose leaks?", "options": ["Ignore it", "Report and do not start", "Start slowly"], "answer_index": 1}
    ],
}

TELEMETRY_DATA = {
    "engine_rpm": 1850,
    "hydraulic_temp_c": 62.5,
    "fuel_pct": 71,
    "load_pct": 45,
    "speed_kmh": 0.0,
    "idle_seconds": 0,
    "seatbelt": True,
    "proximity_m": 14.2,
}
