# ReBase — API + Internal Contract (v1.1)

Single source of truth between **Person A (AI + UI)** and **Person B (Infra)**. Change only via the protocol in `CLAUDE.md` §6.
B copies the JSON examples below into `app/assets/mock/` as mock fixtures. §6 defines the code-level interfaces (Python functions, Flutter providers) between the two halves.

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

---

## 2. Enums

| Enum | Values |
|---|---|
| `MachineType` | `excavator`, `wheel_loader`, `drill_rig`, `dump_truck` |
| `MachineStatus` | `available`, `in_use`, `maintenance` |
| `Experience` | `novice`, `intermediate`, `expert` |
| `Lang` | `en-IN`, `hi-IN`, `ta-IN`, `te-IN` |
| `JobStatus` | `scheduled`, `in_progress`, `done` |
| `Shift` | `day`, `night` |
| `RestStatus` | `ok`, `warning`, `must_rest` |
| `SessionState` | `pre_start`, `briefing`, `active`, `ended` |
| `ChecklistStatus` | `pending`, `ok`, `defect`, `na` |
| `AlertType` | `seatbelt_off`, `drowsiness`, `distraction`, `operator_absent`, `proximity`, `excessive_idle`, `overheat`, `overload`, `unsafe_operation` |
| `Severity` | `info`, `warning`, `critical` |
| `OperatorState` | `alert`, `drowsy`, `distracted`, `absent` |
| `SimEvent` | any `AlertType` value, or `normal` |

---

## 3. Endpoint list

"Owner" = who writes the route. "Uses" = code from the other person that the route calls (see §6).

| # | Method | Path | Purpose | Owner | Uses | Milestone |
|---|---|---|---|---|---|---|
| E1 | GET | `/health` | `{"status":"ok","version":"1.1"}` | B | — | M0 |
| E2 | POST | `/auth/login` | `{operator_id, pin}` → `Operator` or 401 `BAD_PIN` | B | — | M1 |
| E3 | GET | `/operators` | List `Operator` | B | — | M1 |
| E4 | GET | `/operators/{id}` | One `Operator` (hours + rest) | B | — | M1 |
| E5 | GET | `/operators/{id}/assignments?range=day\|week\|month` | List `Assignment` | B | — | M1 |
| E6 | GET | `/machines`, `/machines/{id}` | `Machine` | B | — | M1 |
| E7 | GET | `/jobs/{id}` | `Job` | B | — | M1 |
| E8 | GET | `/jobs/{id}/estimate` | `Estimate` | **A** | B's DB models | M2 |
| E9 | POST | `/assignments` | Manager creates assignment (Swagger only) | B | — | M2 |
| E10 | POST | `/sessions` | `{operator_id, machine_id, job_id}` → `Session`; 409 `REST_REQUIRED` | B | — | M3 |
| E11 | GET | `/sessions/{id}` | `Session` | B | — | M3 |
| E12 | GET | `/sessions/{id}/checklist` | `Checklist` | B | A's `load_checklist()` | M3 |
| E13 | PUT | `/sessions/{id}/checklist/items/{item_id}` | `{status, note?}` → `ChecklistItem` | B | — | M3 |
| E14 | POST | `/sessions/{id}/checklist/complete` | → `Session` (`briefing`) or 422 `CHECKLIST_INCOMPLETE` / `CRITICAL_DEFECT` | B | — | M3 |
| E15 | GET | `/sessions/{id}/briefing?lang=` | `Briefing` | **A** | B's DB models | M3 |
| E16 | POST | `/sessions/{id}/start` | → `Session` (`active`) | B | — | M3 |
| E17 | POST | `/sessions/{id}/end` | → `SessionSummary` | B | — | M3 |
| E18 | GET | `/sessions/{id}/alerts` | List `Alert` | B | — | M3 |
| E19 | POST | `/alerts/{id}/ack` | → `Alert` | B | — | M3 |
| W1 | WS | `/ws/sessions/{id}` | Telemetry + alerts (§5) | B | — | M3 |
| E20 | POST | `/assistant/ask` | `AssistantRequest` → `AssistantAnswer` | **A** | B's DB models | M4 |
| E21 | POST | `/voice/stt` | multipart `file` (wav 16 kHz mono) + `lang` → `{"text","lang"}` | **A** | — | M4 |
| E22 | POST | `/voice/tts` | `{text, lang}` → `audio/wav` bytes | **A** | — | M4 |
| E23 | GET | `/operators/{id}/training/next?machine_type=` | `TrainingModule` | B | — | M4 |
| E24 | POST | `/training/{module_id}/complete` | `{operator_id, score}` → `{"ok": true}` | B | — | M4 |
| E25 | GET | `/sim/scenarios` | List of `SimEvent` | B | — | M3 |
| E26 | POST | `/sim/scenario` | `{session_id, event}` → 202 | B | — | M3 |

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

### Estimate
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

### Briefing
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

### Alert
```json
{
  "id": "alr_001",
  "session_id": "ses_001",
  "type": "drowsiness",
  "severity": "critical",
  "message": "Operator eyes closed for more than 2 seconds",
  "ts": "2026-09-24T05:12:44Z",
  "acknowledged": false
}
```

### AssistantRequest / AssistantAnswer
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

## 5. WebSocket `/ws/sessions/{id}`

Server → client, every 1 second while session is `active`:
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
    "proximity_m": 14.2,
    "operator_state": "alert"
  }
}
```
Server → client, when a safety rule fires:
```json
{"type": "alert", "alert": { "...": "Alert object" }}
```
Client → server:
```json
{"type": "ack", "alert_id": "alr_001"}
```
If the session is not `active`, the server sends `{"type": "error", "code": "SESSION_NOT_ACTIVE"}` and closes.

---

## 6. Internal interfaces (code level)

These are the only places where one person's code imports the other's. Signatures here are frozen like HTTP endpoints. **Each owner commits a working stub at M0** (returning the §4 example data) so nobody is blocked.

### 6.1 Backend — B provides, A imports (never edits)

```python
# backend/app/db.py
def get_db() -> Iterator[Session]            # FastAPI dependency (SQLModel session)

# backend/app/models.py  — SQLModel tables, field names = §4 schemas
Operator, Machine, Job, Project, Assignment, WorkSession, ChecklistRecord, Alert, TrainingRecord

class JobLog(SQLModel, table=True):          # history for A's estimator
    id: str
    job_id: str
    operator_id: str
    machine_type: str                        # MachineType
    planned_hours: float
    actual_hours: float
    weather: str                             # "clear" | "rain" | "heat" | "dust"
    operator_experience: str                 # Experience
    date: date
```
B's `main.py` mounts A's router once at M0: `app.include_router(ai_router)` from `app.ai.router`.

### 6.2 Backend — A provides, B imports (never edits)

```python
# backend/app/ai/router.py
router: APIRouter                             # contains E8, E15, E20, E21, E22

# backend/app/ai/api.py
def load_checklist(machine_type: str) -> dict
    # returns {"standard_refs": [...], "sections": [{"title", "items": [{"id","text","critical"}]}]}
    # B adds "status"/"note" per session and stores them
```

### 6.3 Flutter — B provides, A uses (never edits)

```dart
// lib/core/api/api_client.dart
abstract class ApiClient { /* one method per endpoint E1–E26, returning §4 models */
  Future<String> stt(Uint8List wav, String lang);   // E21
  Future<Uint8List> tts(String text, String lang);  // E22
}
final apiClientProvider = Provider<ApiClient>(...);           // mock or http by USE_MOCK

// lib/core/api/ws_client.dart
final sessionStreamProvider = StreamProvider.family<SessionEvent, String>(...); // telemetry | alert
void ackAlert(String sessionId, String alertId);

// lib/core/models/*.dart   — one class per §4 schema, fromJson/toJson
// lib/features/training/training_hub_screen.dart
class TrainingHubScreen extends StatelessWidget { const TrainingHubScreen({required this.operatorId, required this.machineType}); }
```

### 6.4 Flutter — A provides, B uses (never edits)

```dart
// lib/ui/router.dart
GoRouter buildRouter();                       // includes route '/training' → B's TrainingHubScreen
// lib/ui/theme.dart
class AppTheme { static ThemeData dark(); }
// lib/ui/widgets/  — BigButton, StatusCard, AlertBanner (B's training screens reuse these)
```
Training Hub UI text lives in B's `features/training/training_strings.dart` (a per-language map), so B never edits A's ARB files.

## 7. Change log

| Version | Date | By | Change |
|---|---|---|---|
| v1.0 | M0 | A + B | Initial contract |
| v1.1 | M0 | A + B | Re-split: A = AI + UI, B = Infra. Added Owner column, §6 internal interfaces, `JobLog` model |
