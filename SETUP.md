# ReBase — Setup, Run, Test

> Maintained by Claude Code per `CLAUDE.md` §9. Edit only the sections tagged with your owner letter.
> Every step = a command you can copy + one line saying what it does.
> Architecture is v2.0 (edge). Commands below are the **planned** ones; each owner verifies and fixes them as they build.

---

## 1. Prerequisites  [Owner: both]

| Tool | Version | Check with |
|---|---|---|
| Git | any | `git --version` |
| Python | 3.11+ | `python --version` |
| Flutter | stable (3.x) | `flutter doctor` |
| Android emulator (tablet profile) or Android tablet | API 30+ | `flutter devices` |
| A device/emulator **with a working front camera** | — | needed for the edge CV demo (A9) |
| Sarvam AI API key (optional) | — | dashboard.sarvam.ai — for cloud TTS/translate |
| LLM API key | — | your provider — for briefing + Q&A |

## 2. First-time setup  [Owner: both]

```bash
git clone <repo-url> rebase && cd rebase        # get the code
cp .env.example .env                             # create your secrets file, then fill in the keys
echo "I am Person A (Edge AI + UI)" > CLAUDE.local.md   # or "I am Person B (Infra + Backend AI)"
```

---

## 3. Backend  [Owner: B]

### 3.1 Install
```bash
cd backend
python3.11 -m venv .venv && source .venv/bin/activate   # isolated Python 3.11 env (Windows: .venv\Scripts\activate). With uv: uv venv --python 3.11 .venv
pip install -r requirements.txt                      # fastapi, xgboost, chromadb, sentence-transformers, ... (downloads torch: ~10 min the first time)
```

### 3.2 Seed the database + build models
```bash
python -m app.seed                       # wipes and refills backend/rebase.db with demo data (incl. ~60 JobLog rows)
python -m app.ai.train_estimator         # trains the XGBoost time estimator → data/models/estimator.json (prints CV error vs planned-hours baseline)
# Both steps also run automatically on server start if the DB is empty / the model file is missing.
# The RAG vector store builds itself in the background on server start (data/manuals/ → data/models/chroma/);
# the first start downloads the embedding model (~90 MB), later starts reuse it. Rebuilt automatically if a manual changes.
```
Re-seed right before a demo: all dates and work hours are relative to when the seed runs. (If the DB is empty, the server seeds it automatically on startup.)

Demo logins (PINs are checked but not secure):

| Operator | PIN | Lang | Rest status (demo story) |
|---|---|---|---|
| `op_001` Ravi Kumar | 1234 | ta-IN | ok — hero, excavator job `job_001` today |
| `op_002` Priya Sharma | 2345 | hi-IN | warning — 52 h this week |
| `op_003` Arjun Murugan | 3456 | ta-IN | ok — novice (Training Hub) |
| `op_004` Mohit Verma | 4567 | hi-IN | must_rest — starting a session is blocked (409 `REST_REQUIRED`) |
| `op_005` Sam D'Souza | 5678 | en-IN | ok |

### 3.3 Run
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000   # API + simulator on port 8000
```
Open http://localhost:8000/docs to see and try every endpoint.

### 3.4 Test
```bash
pytest -q                   # runs all backend tests
```

### 3.5 Serve the tablet (backend on a laptop, app on an emulator or tablet)
The person running the backend does this; the app side then follows section 4.3.
```bash
cd backend && source .venv/bin/activate
python -m app.seed                                          # fresh demo data, relative to right now
uvicorn app.main:app --host 0.0.0.0 --port 8000             # 0.0.0.0 = reachable from other devices, not just this laptop
ipconfig getifaddr en0                                      # macOS: this laptop's Wi-Fi IP (Windows: ipconfig; Linux: hostname -I)
```
Then, from where the app runs:

| App runs on | `API_BASE` to use | Check it (in the device's browser) |
|---|---|---|
| Android emulator on the **same laptop** as the backend | `http://10.0.2.2:8000` | http://10.0.2.2:8000/health |
| Real tablet, or an emulator on **another laptop** | `http://<IP from ipconfig>:8000` (same Wi-Fi) | http://<IP>:8000/health → `{"status":"ok","version":"2.0"}` |

If `/health` doesn't load from the other device: both on the same Wi-Fi (not a guest network that isolates devices), and on macOS click **Allow** when asked "accept incoming network connections" for Python (or System Settings → Network → Firewall).

**What the backend serves today** (so you know what's real vs placeholder):

| Area | Endpoints | Status |
|---|---|---|
| Login, operators (hours + rest), machines, jobs, assignments | E2–E7, E9 | ✅ real |
| Job-time estimate (XGBoost) | E8 | ✅ real |
| Sessions, checklist + critical-defect gate, briefing | E10–E17 | ✅ real (briefing = template until a Gemini key is set, section 5.1) |
| Live telemetry WebSocket + scenarios | W1, E21, E22 | ✅ real — `ws://<host>:8000/ws/sessions/{id}`, only while the session is `active` |
| Incident log (alerts), ack | E18–E20 | ✅ real |
| Assistant Q&A (manual RAG + LLM, answers in en/hi/ta) | E23 | ✅ real |
| Cloud TTS / translate (Sarvam) | E24, E25 | ⏳ TTS returns 503 → app uses on-device TTS; translate echoes the text |
| Training Hub content (12 modules: 4 machines × 3 levels) + quiz result | E26, E27 | ✅ real |

Errors always come back as `{"error": {"code": "...", "message": "..."}}` — e.g. `409 REST_REQUIRED` (Mohit), `422 CRITICAL_DEFECT` (hose leak), `409 INVALID_STATE` (step out of order). Order of a session: `checklist complete → briefing → start → end`.

### 3.6 Common errors  [Owner: B]
| Error | Fix |
|---|---|
| `chromadb` / embedding model slow on first run | It downloads the embedding model once; let it finish, then it's cached |
| `TypeError: unsupported operand type(s) for \|` or syntax errors on start | Wrong Python — macOS `python3` is 3.9. Recreate the venv with `python3.11` |
| _(fill in as you hit them)_ | |

---

## 4. App  [Owner: A]

> Edited by B (2026-09-24, with B's human's OK) to add device selection + APK build. **A: please verify on your machine and adjust freely** — this section stays yours.

### 4.1 Install
```bash
flutter doctor                 # Flutter + Android toolchain OK (fix anything red first)
cd app
flutter pub get                # install Dart packages (incl. google_mlkit_face_detection, speech_to_text, flutter_tts)
flutter devices                # your emulator / tablet is listed (real tablet: enable USB debugging, plug in, accept the prompt)
```

### 4.2 Run on mock data (no backend needed)
```bash
flutter run --dart-define=USE_MOCK=true                     # whole app on built-in fake data; camera CV still runs on-device
```

### 4.3 Run against the real backend
The backend must be running and reachable first — see section 3.5 (host `0.0.0.0`, laptop IP, `/health` check).
```bash
# Android emulator on the SAME laptop as the backend (10.0.2.2 = "the computer running the emulator"):
flutter run -d <device-id> --dart-define=USE_MOCK=false --dart-define=API_BASE=http://10.0.2.2:8000
# Real tablet (or an emulator on another laptop), same Wi-Fi as the backend laptop:
flutter run -d <device-id> --dart-define=USE_MOCK=false --dart-define=API_BASE=http://<laptop-ip>:8000
```
Log in as `op_001` Ravi Kumar, PIN `1234` (all demo logins: section 3.2). `<device-id>` comes from `flutter devices`.

### 4.4 Build an APK to install on the tablet
`API_BASE` is fixed into the APK when it's built — rebuild if the laptop's IP changes.
```bash
flutter build apk --debug --dart-define=USE_MOCK=false --dart-define=API_BASE=http://<laptop-ip>:8000   # builds the installable app
adb install -r build/app/outputs/flutter-apk/app-debug.apk                                                # installs it on the connected tablet
```

### 4.5 Test
```bash
flutter analyze             # static checks, must be clean
flutter test                # widget/unit/edge tests
```

### 4.6 Common errors  [Owner: both — add rows only]
| Error | Fix |
|---|---|
| App can't reach backend on emulator | Use `10.0.2.2`, not `localhost` |
| Cleartext HTTP blocked on Android | Add `android:usesCleartextTraffic="true"` to AndroidManifest (demo only) |
| Camera permission denied (edge CV) | Grant camera permission; the CV demo needs the front camera |
| Tablet can't reach the laptop backend | Backend started with `--host 0.0.0.0`; same Wi-Fi; open `http://<laptop-ip>:8000/health` in the tablet browser; allow Python through the macOS firewall (section 3.5) |
| `409 REST_REQUIRED` when starting a session | Expected for `op_004` Mohit (fatigue demo). Use `op_001` Ravi / PIN 1234 for the main flow |
| `409 INVALID_STATE` / `SESSION_ALREADY_ACTIVE` | A step was called out of order, or the operator still has an active session — end it (`POST /sessions/{id}/end`) or re-seed (`python -m app.seed`) |
| `503 UPSTREAM_UNAVAILABLE` from `/voice/tts` | Expected until Sarvam is set up — use on-device `flutter_tts` |
| Gauges don't react to `POST /sim/scenario` | The app must read the real WebSocket (`ws://<host>:8000/ws/sessions/{id}`), and the session must be `active` (after Start) |
| _(fill in as you hit them)_ | |

---

## 5. AI / voice keys  [Owner: B]

### 5.1 Keys
All keys are optional — the demo runs with none. Speech-to-text and text-to-speech run on the tablet. Without an LLM key the briefing uses a template and the assistant reads the matching English manual section. `SARVAM_API_KEY` is unused for now (Sarvam voices are postponed, B12): `/voice/tts` answers 503 so the app uses its own voice.

**LLM is optional and free.** Default `LLM_PROVIDER=gemini` (Google Gemini free tier, model `gemini-3.5-flash-lite`, falls back to `gemini-3.8-flash` when busy): get a key at https://aistudio.google.com/apikey and put it in `LLM_API_KEY`. `LLM_PROVIDER=anthropic` also works. **Fallback:** also set `GROQ_API_KEY` (free, console.groq.com) and any Gemini failure (overloaded, quota, timeout) is retried on Groq `openai/gpt-oss-120b` automatically. With no key, the briefing (E15) uses a built-in template with en/hi/ta phrases — the demo works fully without any LLM key.

### 5.2 Re-train the estimator (after any re-seed)
```bash
cd backend && python -m app.ai.train_estimator   # writes data/models/estimator.json
```

### 5.3 Quick checks
```bash
curl -X POST localhost:8000/assistant/ask -H "Content-Type: application/json" \
  -d '{"machine_id":"mc_001","question":"पावर मोड में कैसे बदलें?","lang":"hi-IN"}'   # manual Q&A
# With an LLM key: a Hindi answer + "sources":[{"doc":"excavator_manual.md","section":"4.2 Operating modes"}]
# Without a key:   Hindi/Tamil questions get "not found in the manual" (they need the LLM to translate);
#                  English questions get the matching English manual text with "lang":"en-IN"
curl -X POST localhost:8000/voice/tts -H "Content-Type: application/json" \
  -d '{"text":"नमस्ते","lang":"hi-IN"}'   # expect 503 UPSTREAM_UNAVAILABLE until Sarvam (B12) — the app then uses on-device TTS
```

### 5.4 Common errors  [Owner: B]
| Error | Fix |
|---|---|
| Hindi/Tamil questions get "language service unavailable" (or English answers / template briefing) | The server can't reach an LLM. Look at the **first lines of the server console**: `LLM: gemini ✓ key set → groq ✓ key set` is good; `✗ NO KEY` means that server's `.env` has no `LLM_API_KEY`/`GROQ_API_KEY` — add them and restart. Each fallback also logs a `[app.ai.assistant]` line saying why. Make sure the app's `API_BASE` points at the server that has the keys |
| _(fill in as you hit them)_ | |

## 6. Run the full stack  [Owner: both]

1. Terminal 1: backend (3.3).
2. Terminal 2: app against real backend (4.3), or the installed APK (4.4).
3. Log in, start a session, then trigger scenarios (section 7). Point the tablet camera at a face for the CV alert.

## 7. Demo scenario triggers  [Owner: B]

Run on the backend laptop once the tablet has **started** the session (state `active`). The session id is shown by the app, or is the latest `ses_NNN` (`curl localhost:8000/sessions/ses_001` … shows each one's state).
```bash
SID=ses_001                                   # the active session
curl -X POST localhost:8000/sim/scenario -H "Content-Type: application/json" \
  -d "{\"session_id\":\"$SID\",\"event\":\"seatbelt_off\"}"   # steers telemetry so the TABLET's rule fires the alert
```
Or use Swagger: `/docs` → `POST /sim/scenario`.

| Event | What the stream does (~15 s, then back to normal) | Tablet rule that should fire |
|---|---|---|
| `seatbelt_off` | `seatbelt` → false | seatbelt (critical if moving) |
| `proximity` | `proximity_m` 9 → 1.5 m | proximity: warning (<5 m), then critical (<2 m) |
| `overheat` | `hydraulic_temp_c` 88 → 108 °C | overheat: warning (>95), then critical (>105) |
| `overload` | `load_pct` 85 → 104 % | overload: warning (>90), then critical (>100) |
| `unsafe_operation` | 18 km/h at 85 % load | unsafe operation |
| `excessive_idle` | idle, `idle_seconds` 170 → 185 | excessive idle (fires ~10 s in) |
| `normal` | cancels the running scenario | — |

A new event replaces the one running. Camera events (`drowsiness`, `distraction`, `operator_absent`) are triggered **live** by a real face in front of the tablet — the API accepts them but doesn't change telemetry.

Watch the raw stream on the laptop (optional, handy when the tablet shows nothing):
```bash
cd backend && SID=ses_001 .venv/bin/python -c "
import asyncio, json, os, websockets
async def main():
    async with websockets.connect(f'ws://localhost:8000/ws/sessions/{os.environ[\"SID\"]}') as ws:
        async for m in ws: print(json.loads(m))
asyncio.run(main())"
```

## 8. Fresh-clone check  [Owner: both — B leads at M5]

- [x] **Backend** (B, 2026-09-24): sections 2–3 followed literally in a clean copy of the repo (no `.env` keys, no DB, no models, new venv): install ✅ (~9 min), seed + train ✅, `pytest` 215/215 ✅, server + scripted demo flow 20/20 ✅ (login, fatigue cast, estimate, Mohit blocked, hose-leak gate, Tamil briefing, live WS + scenario, alert + ack, assistant, training, TTS 503, summary). Caveat: the embedding model was already in the local cache — on a new machine the first server start also downloads it (~90 MB)
- [ ] **App** (A): sections 4 + 6 in a new folder, no step failed
- [ ] Final run of both at M5 (after the last commits)
- [ ] Mock mode works with backend off
- [ ] Edge CV fires a real alert from the camera; telemetry scenarios fire on-device rules
- [ ] All demo scenarios in `docs/DEMO.md` work
