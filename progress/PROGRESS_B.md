# Progress — Person B (Infra)

> Only Person B edits this file. Person A reads it.
> Status: ⬜ todo · 🟨 doing · ✅ done (matches CONTRACT, tested) · 🟦 done on mock/stub only · ⛔ blocked · ➡️ moved

**Last updated:** —  **Current milestone:** M0  **Contract version in use:** v1.1

## Tasks

| ID | Task | Side | Endpoints / provides | Milestone | Status | Notes |
|---|---|---|---|---|---|---|
| B0 | Scaffold: FastAPI skeleton + `/health`, `db.py`, `models.py` (incl. `JobLog`), mount `ai_router`; `flutter create`, `pubspec.yaml` with A block, `main.dart`, `core/config.dart` | Both | E1 | M0 | ⬜ | Blocks A at M0 — do first |
| B1 | Seed: 4 machines, ~5 operators, 2 projects, ~8 jobs, ~60 `JobLog` rows | Backend | — | M1 | ⬜ | A5 depends on this |
| B2 | Core endpoints: login, operators, machines, jobs, assignments | Backend | E2–E7, E9 | M1 | ⬜ | |
| B3 | Fatigue / rest service | Backend | in E4, E10 | M1 | ⬜ | |
| B4 | Flutter data layer: models, `ApiClient`, `MockApiClient` + fixtures + fake WS, providers | App | §6.3 | M1 | ⬜ | A's screens depend on this |
| B5 | `HttpApiClient` for all endpoints (incl. multipart STT, binary TTS) | App | §6.3 | M2 | ⬜ | |
| B6 | Sessions + checklist status + critical-defect gate (uses A's `load_checklist`) | Backend | E10–E14 | M3 | ⬜ | |
| B7 | Simulator engine + scenarios | Backend | E25, E26 | M3 | ⬜ | |
| B8 | WebSocket + safety rule engine + alert log + ack; Flutter `WsClient` | Both | W1, E16–E19 | M3 | ⬜ | |
| B9 | Training content YAML (4 types × 3 levels, start with excavator) + endpoints | Backend | E23, E24 | M4 | ⬜ | |
| B10 | Training Hub screens: steps, video links, quiz, complete, 4 languages | App | E23, E24 | M4 | ⬜ | Uses A's theme/widgets |
| B11 | Tests (`tests/infra`, core tests) + SETUP Backend/App sections + lead fresh-clone check | Both | — | M5 | ⬜ | |

## Ready for A
_(e.g. "B0 models + get_db pushed @ abc123", "E2–E7 live on main")_

## Blockers
_None_

## Requests for partner (A)
_None_

## Session log
| When | Did | Next |
|---|---|---|
