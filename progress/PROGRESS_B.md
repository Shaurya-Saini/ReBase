# Progress — Person B (Infra + Backend AI)

> Only Person B edits this file. Person A reads it.
> Status: ⬜ todo · 🟨 doing · ✅ done (matches CONTRACT, tested) · 🟦 done on mock/stub only · ⛔ blocked · ➡️ moved
> B owns all backend + the Flutter data layer + Training Hub screens.

**Last updated:** —  **Current milestone:** M0  **Contract version in use:** v2.0

## Tasks

| ID | Task | Endpoints / provides | Milestone | Status | Notes |
|---|---|---|---|---|---|
| B0 | Scaffold: FastAPI skeleton + `/health`, `db.py` (`get_db`), `models.py` (incl. `JobLog`), config, all routers stubbed; `flutter create`, `pubspec.yaml` with A block, `main.dart`, `core/config.dart` | E1 | M0 | ⬜ | Blocks A at M0 — do first |
| B1 | Seed: 4 machines, ~5 operators, 2 projects, ~8 jobs, ~60 `JobLog` rows (varied weather/experience/actual-vs-planned) | — | M1 | ⬜ | B6 depends on this |
| B2 | Core endpoints: login, operators, machines, jobs, assignments | E2–E7, E9 | M1 | ⬜ | |
| B3 | Fatigue / rest service (feeds E4, gate at E10) | in E4, E10 | M1 | ⬜ | |
| B4 | Flutter data layer: models (incl. `AlertCreate`, `Telemetry`), `ApiClient`, `MockApiClient` + fixtures, `telemetryStreamProvider` (fake 1 Hz telemetry), providers | §6.1 | M1 | ⬜ | A's screens depend on this |
| B5 | `HttpApiClient` for all endpoints (incl. binary TTS, alert POST) | §6.1 | M2 | ⬜ | |
| B6 | **XGBoost estimator**: train on `JobLog`, fallback formula, E8 + `train_estimator` script | E8 | M2 | ⬜ | Needs B1 seed |
| B7 | Sessions + checklist status + critical-defect gate + briefing (LLM + template fallback) | E10–E17 | M3 | ⬜ | Uses B10 checklist content |
| B8 | Simulator engine + scenarios + WebSocket **telemetry stream** (no server-side alerts) | W1, E21, E22 | M3 | ⬜ | `POST /sim/scenario` steers values so A's rules fire |
| B9 | Alert storage + list + ack (receives A's on-device alerts) | E18, E19, E20 | M3 | ⬜ | Incident log |
| B10 | **RAG**: ChromaDB vector store + `sentence-transformers`; ingest manuals + checklist content; serve checklist (E12) | E12 | M3 | ⬜ | Checklists structured; RAG for Q&A |
| B11 | **Q&A assistant** (E23) via RAG + LLM, answers in `lang`, returns sources | E23 | M4 | ⬜ | |
| B12 | Sarvam proxy: TTS (E24) + translate (E25); 503 on missing key/timeout, never crash | E24, E25 | M4 | ⬜ | Check docs.sarvam.ai for current models |
| B13 | Training content YAML (4 types × 3 levels, start with excavator) + endpoints | E26, E27 | M4 | ⬜ | |
| B14 | Training Hub screens: steps, video links, quiz, complete, 3 languages (`training_strings.dart`) | E26, E27 | M4 | ⬜ | Uses A's theme/widgets |
| B15 | Tests (`tests/`, `test/core`, `test/features/training`) + SETUP Backend/App sections + lead fresh-clone check | — | M5 | ⬜ | |

## Ready for A
_(e.g. "B0 models + get_db pushed @ abc123", "E2–E7 live on main", "fake telemetry stream in MockApiClient")_

## Blockers
_None_

## Requests for partner (A)
_None_

## Session log
| When | Did | Next |
|---|---|---|
