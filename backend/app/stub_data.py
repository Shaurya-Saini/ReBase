"""B0 stubs: the CONTRACT.md §4 JSON examples, verbatim.

Routers return these until the real implementation (B1–B13) replaces them.
Delete entries as they stop being used.
"""

OPERATOR = {
    "id": "op_001",
    "name": "Ravi Kumar",
    "lang": "ta-IN",
    "experience": {"excavator": "expert", "wheel_loader": "novice"},
    "hours_today": 3.5,
    "hours_7d": 41.0,
    "rest": {"status": "ok", "next_allowed_start": None, "reason": None},
}

MACHINE = {
    "id": "mc_001",
    "type": "excavator",
    "model": "Generic 20t Excavator",
    "serial": "EX20-0001",
    "hour_meter": 4521.3,
    "status": "available",
    "last_inspection": "2026-09-23T02:10:00Z",
}

JOB = {
    "id": "job_001",
    "project_id": "prj_001",
    "title": "Trench excavation – Block C",
    "site": "Site 2, North Pit",
    "machine_type": "excavator",
    "scheduled_start": "2026-09-24T03:30:00Z",
    "planned_hours": 6.0,
    "status": "scheduled",
}

ASSIGNMENT = {
    "id": "asg_001",
    "operator_id": "op_001",
    "date": "2026-09-24",
    "shift": "day",
    "job": JOB,
    "machine": MACHINE,
}

ESTIMATE = {
    "job_id": "job_001",
    "estimated_hours": 6.8,
    "range_hours": [5.9, 7.6],
    "factors": [
        {"name": "weather", "effect_pct": 8, "note": "Light rain forecast"},
        {"name": "operator_experience", "effect_pct": -5, "note": "Expert on excavator"},
    ],
    "project_completion_date": "2026-10-18",
}

SESSION = {
    "id": "ses_001",
    "operator_id": "op_001",
    "machine_id": "mc_001",
    "job_id": "job_001",
    "state": "pre_start",
    "started_at": None,
    "ended_at": None,
}

SESSION_SUMMARY = {
    "session_id": "ses_001",
    "duration_hours": 5.9,
    "alerts_total": 4,
    "alerts_critical": 1,
    "idle_minutes": 22,
}

CHECKLIST = {
    "session_id": "ses_001",
    "machine_type": "excavator",
    "standard_refs": ["MSHA 30 CFR 56.14100", "ISO 20474"],
    "sections": [
        {
            "title": "Walk-around",
            "items": [
                {"id": "chk_01", "text": "Check tracks and undercarriage for damage", "critical": False, "status": "pending", "note": None},
                {"id": "chk_02", "text": "Check hydraulic hoses for leaks", "critical": True, "status": "pending", "note": None},
            ],
        }
    ],
}

BRIEFING = {
    "session_id": "ses_001",
    "lang": "en-IN",
    "machine_summary": "20t excavator, 4521 hours, last inspection today.",
    "job_summary": "Dig 40 m trench, 1.5 m deep, Block C.",
    "estimated_hours": 6.8,
    "hazards": ["Overhead power line near east edge", "Soft ground after rain"],
    "reminders": ["Keep 10 m distance from ground crew"],
}

ALERT = {
    "id": "alr_001",
    "session_id": "ses_001",
    "type": "drowsiness",
    "source": "edge_cv",
    "severity": "critical",
    "message": "Operator eyes closed for more than 2 seconds",
    "ts": "2026-09-24T05:12:44Z",
    "acknowledged": False,
}

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
