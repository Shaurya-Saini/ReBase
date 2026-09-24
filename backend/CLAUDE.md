# backend/CLAUDE.md — Person B (Infra + Backend AI)

Read the root `CLAUDE.md` first. In v2.0 **Person B owns the entire `backend/`** (Person A writes no backend code). The AI parts (RAG, estimator, briefing, Sarvam proxy) have their own guide: `backend/app/ai/CLAUDE.md`.

## Layout

```
backend/
├── requirements.txt           fastapi, uvicorn, sqlmodel, python-multipart, pyyaml, pytest, httpx,
│                              xgboost, scikit-learn, chromadb, sentence-transformers
├── app/
│   ├── main.py                FastAPI app, CORS (allow all), includes all routers,
│   │                          startup: create tables + start simulator + warm RAG store
│   ├── config.py              settings from repo-root .env + fatigue defaults + Sarvam/LLM keys
│   ├── db.py                  engine (SQLite backend/rebase.db) + get_db()
│   ├── models.py              all tables incl. JobLog + Alert
│   ├── seed.py                `python -m app.seed` → wipe + refill DB (incl. ~60 JobLog rows)
│   ├── schemas.py             API request/response shapes = CONTRACT §2 enums + §4 schemas
│   ├── errors.py              ApiError + handlers → {"error": {"code", "message"}} (§1)
│   ├── i18n.py                display text in hi/ta from data/i18n (?lang= / Accept-Language, CONTRACT v2.2)
│   ├── routers/               operators (incl. /auth/login), machines, jobs, assignments, sessions,
│   │                          checklist, alerts, training, sim, ws   (assistant + voice live in ai/)
│   ├── services/
│   │   ├── fatigue.py         hours_today, hours_7d, rest status (E4, E10 gate)
│   │   └── sessions.py        session state machine + checklist status + critical-defect gate (E14)
│   ├── simulator/
│   │   ├── engine.py          async loop per active session, 1 Hz, pushes TELEMETRY to WS
│   │   └── scenarios.py       SimEvent → telemetry changes (no alerts — the tablet decides those)
│   └── ai/                    RAG, estimator, briefing, Sarvam — see backend/app/ai/CLAUDE.md
├── data/checklists/           <machine_type>.yaml  (structured checklist content, served by E12)
├── data/manuals/              <machine_type>_manual.md  (embedded in the vector DB for Q&A)
├── data/training/             <machine_type>_<level>.yaml
├── data/i18n/                 hi-IN.yaml, ta-IN.yaml — translations of seeded + checklist display text
├── data/fonts/                Noto Sans (Latin/Tamil/Devanagari, SIL OFL) for video lessons
├── data/models/               estimator.json (XGBoost) + chroma/ store  (gitignored)
└── tests/                     pytest + TestClient, one file per router/service
```

## Rules

- `models.py`, `get_db()`, and every route signature are in `CONTRACT.md` — changing them is a contract change.
- **v2.0: the simulator streams telemetry only.** It never emits alerts. `POST /sim/scenario` steers telemetry values (e.g. `seatbelt=false`, low `proximity_m`, high `hydraulic_temp_c`) so the **tablet's** rule engine fires. Do **not** put `operator_state` in telemetry — camera CV owns operator state on-device.
- **Alerts are created by the app** (E18 `POST /sessions/{id}/alerts`). B validates, stores, timestamps, and serves them (E19) + ack (E20). This is the incident log.
- **Checklists** come from `data/checklists/*.yaml` via the RAG/content layer; B stores per-session status/notes and enforces the critical-defect gate at E14.
- **Fatigue gate:** E10 returns 409 `REST_REQUIRED` when the operator's hours violate the configured limits.
- Simulator must be demo-friendly: normal values with small noise; a scenario nudge lasts ~10 s then returns to `normal`.
- M0 duty: commit `db.py`, `models.py` (tables can be minimal but `JobLog`/`Alert` fields must match §4), all routers stubbed returning §4 example data. (Since v2.1 the Flutter `core/` stubs are A's — B writes no Flutter code.)
- Run `pytest -q` before every merge to `main`.
- Python 3.11 venv: `uv venv --python 3.11 .venv` (or `python3.11 -m venv .venv`) — the macOS system `python3` is 3.9 and too old.
