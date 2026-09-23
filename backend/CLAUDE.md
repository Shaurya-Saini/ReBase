# backend/CLAUDE.md — Person B (Infra)

Read the root `CLAUDE.md` first. Person B owns everything in `backend/` **except** `app/ai/`, `data/checklists/`, `data/manuals/`, `data/models/`, `tests/ai/` and `requirements-ai.txt` (Person A — see `app/ai/CLAUDE.md`).

## Layout (B's parts)

```
backend/
├── requirements.txt           fastapi, uvicorn, sqlmodel, pyyaml, pytest, httpx
├── app/
│   ├── main.py                FastAPI app, CORS (allow all), includes B's routers + A's `ai_router`,
│   │                          startup: create tables + start simulator
│   ├── config.py              B's settings from repo-root .env + fatigue defaults
│   ├── db.py                  engine (SQLite backend/rebase.db) + get_db()   ← A imports
│   ├── models.py              all tables incl. JobLog                        ← A imports
│   ├── seed.py                `python -m app.seed` → wipe + refill DB
│   ├── routers/               operators, machines, jobs, assignments, sessions, alerts,
│   │                          training, sim, ws
│   ├── services/
│   │   ├── fatigue.py         hours_today, hours_7d, rest status
│   │   └── safety.py          telemetry → alerts; all thresholds in one THRESHOLDS dict
│   └── simulator/
│       ├── engine.py          async loop per active session, 1 Hz, pushes to WS
│       └── scenarios.py       SimEvent → telemetry changes
├── data/training/             <machine_type>_<level>.yaml
└── tests/infra/               pytest + TestClient, one file per router
```

## Rules

- `models.py` and `get_db()` signatures are in `CONTRACT.md` §6.1 — changing them is a contract change (A imports them).
- M0 duty: commit `db.py`, `models.py` (tables can be minimal but `JobLog` fields must match), and the `include_router(ai_router)` line in `main.py`. If A's stub isn't pushed yet, wrap the import in try/except and log a warning.
- Checklist content comes from A's `load_checklist(machine_type)`; B stores per-session status/notes and enforces the critical-defect gate.
- Seed must produce ~60 `JobLog` rows with varied weather, experience and a realistic spread of actual vs planned hours (A trains on them).
- Simulator must be demo-friendly: normal values with small noise; a scenario lasts ~10 s then returns to `normal`. Each alert fires once per occurrence (debounce).
- Run `pytest tests/infra -q` before every merge to `main`.
