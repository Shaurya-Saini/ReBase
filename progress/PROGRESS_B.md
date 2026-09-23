# Progress — Person B (Infra + Backend AI)

> Only Person B edits this file. Person A reads it.
> Status: ⬜ todo · 🟨 doing · ✅ done (matches CONTRACT, tested) · 🟦 done on mock/stub only · ⛔ blocked · ➡️ moved
> B owns **all backend** (incl. Training Hub content + endpoints). Since v2.1 **all Flutter work moved to A** (DECISIONS #14) — B has no Flutter toolchain.

**Last updated:** 2026-09-23 (ownership re-split v2.1)  **Current milestone:** M0  **Contract version in use:** v2.1

## Tasks

| ID | Task | Endpoints / provides | Milestone | Status | Notes |
|---|---|---|---|---|---|
| B0 | Scaffold: FastAPI skeleton + `/health`, `db.py` (`get_db`), `models.py` (incl. `JobLog`), config, all routers stubbed returning §4 examples | E1 | M0 | ✅ | Do first. Flutter half (`flutter create`, pubspec, `main.dart`, `core/config.dart`) ➡️ moved to A |
| B1 | Seed: 4 machines, ~5 operators, 2 projects, ~8 jobs, ~60 `JobLog` rows (varied weather/experience/actual-vs-planned) | — | M1 | ✅ | B6 depends on this |
| B2 | Core endpoints: login, operators, machines, jobs, assignments | E2–E7, E9 | M1 | ✅ | |
| B3 | Fatigue / rest service (feeds E4, gate at E10) | in E4, E10 | M1 | ✅ | |
| B4 | Flutter data layer: models (incl. `AlertCreate`, `Telemetry`), `ApiClient`, `MockApiClient` + fixtures, `telemetryStreamProvider` (fake 1 Hz telemetry), providers | §6.1 | M1 | ➡️ | Moved to A (v2.1) |
| B5 | `HttpApiClient` for all endpoints (incl. binary TTS, alert POST) | §6.1 | M2 | ➡️ | Moved to A (v2.1) |
| B6 | **XGBoost estimator**: train on `JobLog`, fallback formula, E8 + `train_estimator` script | E8 | M2 | ⬜ | Needs B1 seed |
| B7 | Sessions + checklist status + critical-defect gate + briefing (LLM + template fallback) | E10–E17 | M3 | ⬜ | Uses B10 checklist content |
| B8 | Simulator engine + scenarios + WebSocket **telemetry stream** (no server-side alerts) | W1, E21, E22 | M3 | ⬜ | `POST /sim/scenario` steers values so A's rules fire |
| B9 | Alert storage + list + ack (receives A's on-device alerts) | E18, E19, E20 | M3 | ⬜ | Incident log |
| B10 | **RAG**: ChromaDB vector store + `sentence-transformers`; ingest manuals + checklist content; serve checklist (E12) | E12 | M3 | ⬜ | Checklists structured; RAG for Q&A |
| B11 | **Q&A assistant** (E23) via RAG + LLM, answers in `lang`, returns sources | E23 | M4 | ⬜ | |
| B12 | Sarvam proxy: TTS (E24) + translate (E25); 503 on missing key/timeout, never crash | E24, E25 | M4 | ⬜ | Check docs.sarvam.ai for current models |
| B13 | Training content YAML (4 types × 3 levels, start with excavator) + endpoints | E26, E27 | M4 | ⬜ | |
| B14 | Training Hub screens: steps, video links, quiz, complete, 3 languages (`training_strings.dart`) | E26, E27 | M4 | ➡️ | Moved to A (v2.1). B keeps B13 (content + E26/E27) |
| B15 | Backend tests (`tests/`) + SETUP Backend/AI sections + lead fresh-clone check | — | M5 | ⬜ | Flutter tests + SETUP App section → A |

## Ready for A
- **B0 backend skeleton:** every endpoint E1–E27 + W1 exists and returns the CONTRACT §4 example JSON (stubs). Run it (SETUP §3) and point the app's real client at it; browse/try everything at `http://localhost:8000/docs`. W1 streams the §5 example telemetry every second for any session id. Errors follow §1 (`{"error": {"code", "message"}}`); bad enum values → 422 `VALIDATION_ERROR`. E24 `/voice/tts` returns 503 `UPSTREAM_UNAVAILABLE` until B12 — use on-device `flutter_tts`.
- **B1 seed data** (`python -m app.seed`): IDs `op_001`–`op_005`, `mc_001`–`mc_004` (one per machine type), `prj_001`/`prj_002`, `job_001`–`job_008`, `asg_001`–`asg_008`. Contract example IDs (`op_001` Ravi / `mc_001` / `job_001` / `prj_001`) are real seeded rows, so your mock fixtures line up. Demo logins + PINs + rest-status story are in SETUP §3.2 (`op_001` / 1234 = Ravi, ta-IN). Served live since B2 (below).
- **B2 live on seeded data: E2–E7, E9.** Stubs remain for E8 estimate (B6), sessions/checklist/briefing (B7), W1 + sim (B8), alerts (B9), assistant (B11), voice (B12), training (B13). Notes for your `HttpApiClient`:
  - **B3 live:** `hours_today` = hours in the *current shift* (work with breaks < 10 h counts as one shift; resets to 0 after 10 h rest, so night shifts crossing midnight count correctly). `hours_7d` = rolling 7 days. `rest.status`: `must_rest` at 12 h shift or 60 h/7 d (with `next_allowed_start` + `reason`), `warning` at ≥ 9.6 h shift or ≥ 51 h/7 d (with `reason`), else `ok` (nulls).
  - **E10 gate:** `POST /sessions` for a `must_rest` operator → `409 REST_REQUIRED`, body `{"error": {"code", "message" (= reason), "next_allowed_start": "…Z"}}`. Demo: `op_004` Mohit is always blocked; `op_002` Priya shows `warning` but may start. Rest of E10 (persisting the session) is still a stub until B7.
  - E5 `range`: `day` = today (IST), `week` = today + next 6 days, `month` = today + next 29 days; sorted by date then shift.
  - Error codes (all in the §1 format): E2 `401 BAD_PIN`, `404 OPERATOR_NOT_FOUND`; E4/E5 `404 OPERATOR_NOT_FOUND`; E6 `404 MACHINE_NOT_FOUND`; E7/E8 `404 JOB_NOT_FOUND`; E9 also `422 MACHINE_TYPE_MISMATCH`, `409 ASSIGNMENT_CONFLICT`; bad query/body → `422 VALIDATION_ERROR`.
  - Times are ISO 8601 UTC with `Z` (e.g. `scheduled_start: "…T03:30:00Z"` = 09:00 IST).
  - The server auto-seeds an empty DB on startup; `python -m app.seed` still re-seeds on demand.

## Blockers
_None_

## Requests for partner (A)
1. **Please OK the v2.1 ownership re-split** (DECISIONS #14, CONTRACT v2.1): you now own the whole `app/` — `flutter create app --org com.rebase --platforms android`, `pubspec.yaml`, `main.dart`, `lib/core/` (models + barrel, `ApiClient`/`MockApiClient`/`HttpApiClient`, `telemetryStreamProvider`), `assets/mock/`, and Training Hub screens. No API changes.
2. Please add B0 (Flutter half), B4, B5, B14 to `PROGRESS_A.md` (I can't edit your file), and close your old requests 1, 2, 4 to me — they're yours now.
3. ~~Your request 3 (`.gitignore` for `estimator.json` + `chroma/`)~~ — done in B0.

## Session log
| When | Did | Next |
|---|---|---|
| 2026-09-23 | Created `CLAUDE.local.md` (Person B). Re-split ownership v2.1: whole Flutter app → A (CLAUDE.md §2–4/§9, CONTRACT v2.1, app/CLAUDE.md, backend/CLAUDE.md, SETUP §4, DECISIONS #14). | Get A's OK, then B0 (backend scaffold). |
| 2026-09-23 | B0 ✅: FastAPI app (`main.py`, `config.py`, `db.py`, `models.py` incl. `JobLog`/`Alert`/`ChecklistItemState`, `schemas.py` = §2/§4, `errors.py` = §1), 10 routers + `ai/router_assistant.py` + `ai/router_voice.py` all stubbed with §4 data, W1 stub stream. `tests/test_b0_stubs.py` 15/15 pass; uvicorn boots, `/docs` lists all 26 contract paths + `/health`. `.gitignore` for estimator/chroma. SETUP §3 → python3.11. | B1 seed, then B2 core endpoints + B3 fatigue. |
| 2026-09-23 | B1 ✅: `app/seed.py` — 5 operators (en/hi/ta, fatigue cast: ok / warning 52 h / must_rest after 12 h night), 4 machines, 2 projects, 8 jobs (with weather + hazards), 8 assignments across day/week/month, 23 past ended sessions as work history, 60 `JobLog` rows with a real weather/experience/machine signal. All relative to seed time (IST day). Switched DB convention to tz-aware UTC (SQLModel requires it). `tests/test_seed.py` incl. a 24-hour sweep for overlap/future-work; 48/48 pass. SETUP §3.2 demo logins. | B2 core endpoints on seeded data, then B3 fatigue. |
| 2026-09-23 | B2 ✅: E2 login (401 `BAD_PIN`), E3/E4 operators, E5 assignments (day/week/month from IST today), E6 machines, E7 job, E9 create assignment (type-mismatch 422, operator/machine double-booking 409, `asg_NNN` ids). Shared `views.py` (row→§4 builders, 404 codes), `clock.py` (IST today), `ids.py`, `services/fatigue.py` placeholder for B3. Schemas `from_attributes`. Auto-seed empty DB on startup. `tests/test_core.py`; 58/58 pass; live smoke on a fresh DB OK. | B3 fatigue service (hours + rest + E10 gate). |
| 2026-09-24 | B3 ✅: `services/fatigue.py` — shift grouping (breaks < MIN_REST merge), current-shift hours, rolling 7-day hours, must_rest (shift cap → +10 h; weekly cap → when window clears) / warning (80% shift, 85% week) with reasons. E4 uses it; E10 now returns 409 `REST_REQUIRED` (+ `next_allowed_start`). Seed fix: Ravi's yesterday off so his today-shift never merges with yesterday when seeded at night. `tests/test_fatigue.py` incl. demo-story check at all 24 IST hours; 91/91 pass; live check OK. | B6 XGBoost estimator (E8) — or B7 sessions if A needs the mounted flow first. |
