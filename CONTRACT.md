# ReBase — API + Internal Contract (v2.2)

Single source of truth between **Person A (Edge AI + UI)** and **Person B (Infra + Backend AI)**. Change only via the protocol in `CLAUDE.md` §6.
A copies the JSON examples below into `app/assets/mock/` as mock fixtures. Since v2.1 the split is **A = the entire Flutter app, B = the entire backend**; the HTTP/WS contract (§3–§5) is the only interface between them. §6 lists the Flutter interfaces A builds.

> **v2.0 re-architecture (read this):** Safety detection now runs **on the tablet (A)** — real computer-vision alerts from the front camera (ML Kit) plus threshold rules over streamed telemetry. The backend **simulates machine sensors** and streams them; it no longer decides alerts, it **stores** the alerts the app posts. Checklists, the manual Q&A assistant, and the briefing are served from the **backend RAG (B)**. Estimation is **XGBoost on the backend (B)**. STT is **on-device (A)**; Sarvam is TTS + translate only, proxied by the backend for the demo. No offline/local-cache in the demo.

---

## 1. Conventions

| Item | Rule |
|---|---|
| Base URL | `http://<host>:8000` (Android emulator: `http://10.0.2.2:8000`) |
| Format | JSON, `snake_case` fields |
| Time | ISO 8601 UTC strings, e.g. `2026-09-24T03:30:00Z` |
| IDs | Strings with prefixes: `op_`, `mc_`, `job_`, `prj_`, `asg_`, `ses_`, `chk_`, `alr_`, `trn_` |
| Auth | None (hackathon). Operator picks their profile + 4-digit PIN (checked, not secure) |
| Errors | `{"error": {"code": "SNAKE_UPPER_CODE", "message": "human readable"}}` with proper HTTP status |
| Demo languages | `en-IN`, `hi-IN`, `ta-IN` (whole app switches). `te-IN` stays in the enum, stretch only. |
| Display language (v2.2) | Endpoints that return display text accept an optional `?lang=<Lang>`; if absent, the `Accept-Language` header is used (`ta-IN`, `ta`, `hi-IN,hi;q=0.9` all work); default `en-IN`. Only human-readable strings are translated: operator `name`, machine `model`, job `title`/`site`, checklist section `title` + item `text`, estimate factor `note`, briefing (template path). **IDs, enums, numbers and all field names never change.** Applies to E2–E7, E8, E9, E12, E13 (E15 already takes `lang`). Missing translation → English. |

---

## 2. Enums

| Enum | Values |
|---|---|
| `MachineType` | `excavator`, `wheel_loader`, `drill_rig`, `dump_truck` |
| `MachineStatus` | `available`, `in_use`, `maintenance` |
| `Experience` | `novice`, `intermediate`, `expert` |
| `Lang` | `en-IN`, `hi-IN`, `ta-IN`, `te-IN` (demo uses the first three) |
| `JobStatus` | `scheduled`, `in_progress`, `done` |
| `Shift` | `day`, `night` |
| `RestStatus` | `ok`, `warning`, `must_rest` |
| `SessionState` | `pre_start`, `briefing`, `active`, `ended` |
| `ChecklistStatus` | `pending`, `ok`, `defect`, `na` |
| `AlertType` | `seatbelt_off`, `drowsiness`, `distraction`, `operator_absent`, `proximity`, `excessive_idle`, `overheat`, `overload`, `unsafe_operation` |
| `AlertSource` | `edge_cv` (camera, on-device), `telemetry` (rule over streamed sensors) |
| `Severity` | `info`, `warning`, `critical` |
| `SimEvent` | any `AlertType` value, or `normal` (drives simulated **telemetry**; camera alerts come from the real device) |

**Which alert comes from where (v2.0):**

| Detected on the tablet by **ML Kit camera CV** (`edge_cv`) | Detected on the tablet by **rules over streamed telemetry** (`telemetry`) |
|---|---|
| `drowsiness`, `distraction`, `operator_absent` | `seatbelt_off`, `proximity`, `excessive_idle`, `overheat`, `overload`, `unsafe_operation` |

---

## 3. Endpoint list

"Owner" = who writes the route (all backend routes are **B** in v2.0). "Caller" notes when the tablet-side owner (A) is the one calling it.

| # | Method | Path | Purpose | Owner | Caller | Milestone |
|---|---|---|---|---|---|---|
| E1 | GET | `/health` | `{"status":"ok","version":"2.0"}` | B | — | M0 |
| E2 | POST | `/auth/login` | `{operator_id, pin}` → `Operator` or 401 `BAD_PIN` | B | A app | M1 |
| E3 | GET | `/operators` | List `Operator` | B | A app | M1 |
| E4 | GET | `/operators/{id}` | One `Operator` (hours + rest) | B | A app | M1 |
| E5 | GET | `/operators/{id}/assignments?range=day\|week\|month` | List `Assignment` | B | A app | M1 |
| E6 | GET | `/machines`, `/machines/{id}` | `Machine` | B | A app | M1 |
| E7 | GET | `/jobs/{id}` | `Job` | B | A app | M1 |
| E8 | GET | `/jobs/{id}/estimate` | `Estimate` (XGBoost + fallback) | B | A app | M2 |
| E9 | POST | `/assignments` | Manager creates assignment (Swagger only) | B | — | M2 |
| E10 | POST | `/sessions` | `{operator_id, machine_id, job_id}` → `Session`; 409 `REST_REQUIRED` (fatigue gate) | B | A app | M3 |
| E11 | GET | `/sessions/{id}` | `Session` | B | A app | M3 |
| E12 | GET | `/sessions/{id}/checklist` | `Checklist` (from backend content/RAG store) | B | A app | M3 |
| E13 | PUT | `/sessions/{id}/checklist/items/{item_id}` | `{status, note?}` → `ChecklistItem` | B | A app | M3 |
| E14 | POST | `/sessions/{id}/checklist/complete` | → `Session` (`briefing`) or 422 `CHECKLIST_INCOMPLETE` / `CRITICAL_DEFECT` (defect gate) | B | A app | M3 |
| E15 | GET | `/sessions/{id}/briefing?lang=` | `Briefing` (LLM + template fallback) | B | A app | M3 |
| E16 | POST | `/sessions/{id}/start` | → `Session` (`active`) | B | A app | M3 |
| E17 | POST | `/sessions/{id}/end` | → `SessionSummary` | B | A app | M3 |
| W1 | WS | `/ws/sessions/{id}` | **Simulated telemetry stream** (§5). Server→client only. | B | A app | M3 |
| E18 | POST | `/sessions/{id}/alerts` | App posts an **on-device-detected** alert → stored `Alert`. Body = `AlertCreate`. | B | **A app** | M3 |
| E19 | GET | `/sessions/{id}/alerts` | List `Alert` (incident log) | B | A app | M3 |
| E20 | POST | `/alerts/{id}/ack` | → `Alert` | B | A app | M3 |
| E21 | GET | `/sim/scenarios` | List of `SimEvent` | B | — | M3 |
| E22 | POST | `/sim/scenario` | `{session_id, event}` → 202 (nudges the telemetry stream) | B | — | M3 |
| E23 | POST | `/assistant/ask` | `AssistantRequest` → `AssistantAnswer` (RAG + LLM) | B | A app | M4 |
| E24 | POST | `/voice/tts` | `{text, lang}` → `audio/wav` bytes (Sarvam) | B | A app | M4 |
| E25 | POST | `/translate` | `{text, target, source?}` → `{"text","lang"}` (Sarvam; optional) | B | A app | M4 |
| E26 | GET | `/operators/{id}/training/next?machine_type=` | `TrainingModule` | B | A app | M4 |
| E27 | POST | `/training/{module_id}/complete` | `{operator_id, score}` → `{"ok": true}` | B | A app | M4 |

**Removed in v2.0:** old `/voice/stt` — speech-to-text now runs **on-device (A)** via the `speech_to_text` plugin.

**On-device only (Person A, no HTTP):** ML Kit face-detection CV (`drowsiness`, `distraction`, `operator_absent`); telemetry rule engine (`seatbelt_off`, `proximity`, `excessive_idle`, `overheat`, `overload`, `unsafe_operation`); on-device STT; on-device TTS default (`flutter_tts`), with E24 as an optional cloud upgrade.

## 4. Schemas (JSON examples = mock fixtures)

### Operator
```json
{
  "id": "op_001",
  "name": "Ravi Kumar",
  "lang": "ta-IN",
  "experience": {"excavator": "expert", "wheel_loader": "novice"},
  "hours_today": 3.5,
  "hours_7d": 41.0,
  "rest": {"status": "ok", "next_allowed_start": null, "reason": null}
}
```

### Machine
```json
{
  "id": "mc_001",
  "type": "excavator",
  "model": "Generic 20t Excavator",
  "serial": "EX20-0001",
  "hour_meter": 4521.3,
  "status": "available",
  "last_inspection": "2026-09-23T02:10:00Z"
}
```

### Job
```json
{
  "id": "job_001",
  "project_id": "prj_001",
  "title": "Trench excavation – Block C",
  "site": "Site 2, North Pit",
  "machine_type": "excavator",
  "scheduled_start": "2026-09-24T03:30:00Z",
  "planned_hours": 6.0,
  "status": "scheduled"
}
```

### Assignment
```json
{
  "id": "asg_001",
  "operator_id": "op_001",
  "date": "2026-09-24",
  "shift": "day",
  "job": { "...": "Job object" },
  "machine": { "...": "Machine object" }
}
```

### Estimate  (XGBoost, backend)
```json
{
  "job_id": "job_001",
  "estimated_hours": 6.8,
  "range_hours": [5.9, 7.6],
  "factors": [
    {"name": "weather", "effect_pct": 8, "note": "Light rain forecast"},
    {"name": "operator_experience", "effect_pct": -5, "note": "Expert on excavator"}
  ],
  "project_completion_date": "2026-10-18"
}
```

### Session / SessionSummary
```json
{
  "id": "ses_001",
  "operator_id": "op_001",
  "machine_id": "mc_001",
  "job_id": "job_001",
  "state": "pre_start",
  "started_at": null,
  "ended_at": null
}
```
```json
{
  "session_id": "ses_001",
  "duration_hours": 5.9,
  "alerts_total": 4,
  "alerts_critical": 1,
  "idle_minutes": 22
}
```

### Checklist / ChecklistItem
```json
{
  "session_id": "ses_001",
  "machine_type": "excavator",
  "standard_refs": ["MSHA 30 CFR 56.14100", "ISO 20474"],
  "sections": [
    {
      "title": "Walk-around",
      "items": [
        {"id": "chk_01", "text": "Check tracks and undercarriage for damage", "critical": false, "status": "pending", "note": null},
        {"id": "chk_02", "text": "Check hydraulic hoses for leaks", "critical": true, "status": "pending", "note": null}
      ]
    }
  ]
}
```
Error on complete (422):
```json
{"error": {"code": "CRITICAL_DEFECT", "message": "Critical items have defects", "items": ["chk_02"]}}
```

### Briefing  (LLM, backend)
```json
{
  "session_id": "ses_001",
  "lang": "en-IN",
  "machine_summary": "20t excavator, 4521 hours, last inspection today.",
  "job_summary": "Dig 40 m trench, 1.5 m deep, Block C.",
  "estimated_hours": 6.8,
  "hazards": ["Overhead power line near east edge", "Soft ground after rain"],
  "reminders": ["Keep 10 m distance from ground crew"]
}
```

### Alert / AlertCreate
`Alert` (stored, returned by E18/E19):
```json
{
  "id": "alr_001",
  "session_id": "ses_001",
  "type": "drowsiness",
  "source": "edge_cv",
  "severity": "critical",
  "message": "Operator eyes closed for more than 2 seconds",
  "ts": "2026-09-24T05:12:44Z",
  "acknowledged": false
}
```
`AlertCreate` (body the **app** posts to E18 — the tablet detected it on-device):
```json
{
  "type": "drowsiness",
  "source": "edge_cv",
  "severity": "critical",
  "message": "Operator eyes closed for more than 2 seconds",
  "ts": "2026-09-24T05:12:44Z"
}
```
> `message` is English (for logs). The app shows localized text looked up by alert `type` (A owns the strings).

### AssistantRequest / AssistantAnswer  (RAG + LLM, backend)
```json
{"machine_id": "mc_001", "session_id": "ses_001", "question": "How do I switch to power mode?", "lang": "hi-IN"}
```
```json
{
  "answer": "…(answer in hi-IN)…",
  "lang": "hi-IN",
  "sources": [{"doc": "excavator_manual.md", "section": "4.2 Operating modes"}]
}
```

### TrainingModule
```json
{
  "id": "trn_ex_novice_01",
  "machine_type": "excavator",
  "level": "novice",
  "title": "Excavator basics before your shift",
  "duration_min": 30,
  "steps": [
    {"kind": "text", "content": "The joystick pattern on this machine is ISO.", "url": null},
    {"kind": "video", "content": "Walk-around inspection", "url": "https://example.com/video"},
    {"kind": "tip", "content": "Never swing over the ground crew.", "url": null}
  ],
  "quiz": [
    {"q": "What must you do if a hydraulic hose leaks?", "options": ["Ignore it", "Report and do not start", "Start slowly"], "answer_index": 1}
  ]
}
```

---

## 5. WebSocket `/ws/sessions/{id}`  (telemetry stream only in v2.0)

Server → client, every 1 second while session is `active`. The simulator produces **machine sensors**; **operator state is no longer here** — it is decided on-device by the camera CV.
```json
{
  "type": "telemetry",
  "ts": "2026-09-24T05:12:43Z",
  "data": {
    "engine_rpm": 1850,
    "hydraulic_temp_c": 62.5,
    "fuel_pct": 71,
    "load_pct": 45,
    "speed_kmh": 0.0,
    "idle_seconds": 0,
    "seatbelt": true,
    "proximity_m": 14.2
  }
}
```
- The app's **telemetry rule engine (A)** watches this stream and raises `telemetry`-source alerts (seatbelt/proximity/idle/overheat/overload/unsafe), then POSTs each to **E18**.
- The app's **camera CV (A)** independently raises `edge_cv`-source alerts (drowsiness/distraction/absence) and POSTs them to **E18**.
- **Ack:** the app calls **E20** (`POST /alerts/{id}/ack`).
- If the session is not `active`, the server sends `{"type": "error", "code": "SESSION_NOT_ACTIVE"}` and closes.

> The server does **not** push `{"type":"alert"}` anymore — alert creation moved to the tablet. `POST /sim/scenario` (E22) simply steers the telemetry values (e.g. drops `seatbelt` to `false`, or `proximity_m` low) so the on-device rules fire during the demo. Camera alerts are triggered by a real face in front of the tablet.

---

## 6. Internal interfaces (code level)

**v2.1:** the whole Flutter app is **Person A**; the whole backend is **Person B**. The two halves meet **only over HTTP/WS** (§3–§5). The interfaces below are still the intended app structure, but A owns and may evolve all of them; B only needs the HTTP/WS shapes to match.

### 6.1 Flutter — data layer (A, formerly B)

```dart
// lib/core/api/api_client.dart
abstract class ApiClient { /* one method per endpoint E1–E27, returning §4 models */
  Future<Alert>   postAlert(String sessionId, AlertCreate alert);   // E18 — A logs on-device alerts
  Future<Alert>   ackAlert(String alertId);                         // E20
  Future<Uint8List> tts(String text, String lang);                 // E24 (optional cloud TTS)
  Future<String>    translate(String text, String target);         // E25 (optional)
}
final apiClientProvider = Provider<ApiClient>(...);           // mock or http by USE_MOCK

// lib/core/api/ws_client.dart
final telemetryStreamProvider = StreamProvider.family<Telemetry, String>(...); // §5 telemetry only

// lib/core/models/*.dart   — one class per §4 schema, fromJson/toJson (incl. AlertCreate, Telemetry)
// lib/features/training/training_hub_screen.dart
class TrainingHubScreen extends StatelessWidget { const TrainingHubScreen({required this.operatorId, required this.machineType}); }
```

### 6.2 Flutter — UI (A)

```dart
// lib/ui/router.dart
GoRouter buildRouter();                       // includes route '/training' → TrainingHubScreen
// lib/ui/theme.dart
class AppTheme { static ThemeData dark(); }
// lib/ui/widgets/  — BigButton, StatusCard, AlertBanner (Training Hub reuses these)
```
Training Hub UI text: A's choice (ARB files or `features/training/training_strings.dart`). Module content (steps, quiz) comes from B via E26 and is served in English; translation of module content is A's call (E25 available).

### 6.3 Backend
No cross-person imports — `backend/` is entirely B, `app/` is entirely A. A's on-device edge code (CV, telemetry rules) lives in `app/lib/edge/` and depends only on A's `core/` models + the WS/HTTP contract.

## 7. Change log

| Version | Date | By | Change |
|---|---|---|---|
| v1.0 | M0 | A + B | Initial contract |
| v1.1 | M0 | A + B | Re-split: A = AI + UI, B = Infra. Added Owner column, §6 internal interfaces, `JobLog` model |
| v2.0 | M0 | A + B | Edge re-architecture. Safety detection → tablet (A): ML Kit camera CV + telemetry rules; app POSTs alerts (new E18). WS = telemetry only. Checklists + Q&A + briefing → backend RAG (B). Estimator → XGBoost (B). STT → on-device (A); removed `/voice/stt`. Sarvam = TTS + translate proxy (B). Backend now entirely B; §6 meets only in Flutter. Demo langs en/hi/ta; no local cache. Endpoints renumbered E1–E27. |
| v2.1 | M0 | B (pending A OK) | Ownership only, no API change: **whole Flutter app → A** (project setup, pubspec, main.dart, `core/` data layer + mock/HTTP/WS clients, mock fixtures, Training Hub screens). B = whole backend, no Flutter. E26/E27 caller → A app. §6 reworded accordingly. |
| v2.2 | M4 | B (additive) | Display language: optional `?lang=` / `Accept-Language` on E2–E9, E12, E13 returns hand-translated hi/ta display strings (names, models, job titles/sites, checklist text, estimate notes). No shape changes; default en-IN. |
