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
python -m venv .venv && source .venv/bin/activate    # isolated Python env (Windows: .venv\Scripts\activate)
pip install -r requirements.txt                      # fastapi, xgboost, chromadb, sentence-transformers, ...
```

### 3.2 Seed the database + build models
```bash
python -m app.seed                       # wipes and refills backend/rebase.db with demo data (incl. ~60 JobLog rows)
python -m app.ai.train_estimator         # trains the XGBoost time estimator → data/models/estimator.json
# The RAG vector store builds itself on first server start (ingests data/manuals/ into data/models/chroma/).
```

### 3.3 Run
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000   # API + simulator on port 8000
```
Open http://localhost:8000/docs to see and try every endpoint.

### 3.4 Test
```bash
pytest -q                   # runs all backend tests
```

### 3.5 Common errors  [Owner: B]
| Error | Fix |
|---|---|
| `chromadb` / embedding model slow on first run | It downloads the embedding model once; let it finish, then it's cached |
| _(fill in as you hit them)_ | |

---

## 4. App  [Owner: A]

### 4.1 Install
```bash
cd app
flutter pub get             # install Dart packages (incl. google_mlkit_face_detection, speech_to_text, flutter_tts)
```

### 4.2 Run on mock data (no backend needed)
```bash
flutter run --dart-define=USE_MOCK=true
```

### 4.3 Run against the real backend
```bash
# Emulator: 10.0.2.2 means "the computer running the emulator"
flutter run --dart-define=USE_MOCK=false --dart-define=API_BASE=http://10.0.2.2:8000
# Physical tablet: use your laptop's Wi-Fi IP (same network), e.g. http://192.168.1.20:8000
```

### 4.4 Test
```bash
flutter analyze             # static checks, must be clean
flutter test                # widget/unit/edge tests
```

### 4.5 Common errors  [Owner: both — add rows only]
| Error | Fix |
|---|---|
| App can't reach backend on emulator | Use `10.0.2.2`, not `localhost` |
| Cleartext HTTP blocked on Android | Add `android:usesCleartextTraffic="true"` to AndroidManifest (demo only) |
| Camera permission denied (edge CV) | Grant camera permission; the CV demo needs the front camera |
| _(fill in as you hit them)_ | |

---

## 5. AI / voice keys  [Owner: B]

### 5.1 Keys
Fill `SARVAM_API_KEY`, `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL` in `.env`. Without them, cloud voice/assistant return a clear 503 and everything else still works (STT and default TTS are on-device).

### 5.2 Re-train the estimator (after any re-seed)
```bash
cd backend && python -m app.ai.train_estimator   # writes data/models/estimator.json
```

### 5.3 Quick checks
```bash
curl -X POST localhost:8000/assistant/ask -H "Content-Type: application/json" \
  -d '{"machine_id":"mc_001","question":"How do I switch to power mode?","lang":"hi-IN"}'   # RAG Q&A works
curl -X POST localhost:8000/voice/tts -H "Content-Type: application/json" \
  -d '{"text":"नमस्ते","lang":"hi-IN"}' --output test.wav                                   # Sarvam TTS works
```

### 5.4 Common errors  [Owner: B]
| Error | Fix |
|---|---|
| _(fill in as you hit them)_ | |

## 6. Run the full stack  [Owner: both]

1. Terminal 1: backend (3.3).
2. Terminal 2: app against real backend (4.3).
3. Log in, start a session, then trigger scenarios (section 7). Point the tablet camera at a face for the CV alert.

## 7. Demo scenario triggers  [Owner: B]

```bash
curl -X POST localhost:8000/sim/scenario -H "Content-Type: application/json" \
  -d '{"session_id":"<ses_id>","event":"seatbelt_off"}'   # steers telemetry so the TABLET's rule fires the alert
```
Telemetry events (steer the stream): `normal`, `seatbelt_off`, `proximity`, `excessive_idle`, `overheat`, `overload`, `unsafe_operation`.
Camera events (`drowsiness`, `distraction`, `operator_absent`) are triggered **live** by a real face in front of the tablet — no curl needed.
Or use Swagger: `/docs` → `POST /sim/scenario`.

## 8. Fresh-clone check  [Owner: both — B leads at M5]

- [ ] Followed sections 2–6 in a new folder, no step failed
- [ ] Mock mode works with backend off
- [ ] Edge CV fires a real alert from the camera; telemetry scenarios fire on-device rules
- [ ] All demo scenarios in `docs/DEMO.md` work
