# ReBase — Setup, Run, Test

> Maintained by Claude Code per `CLAUDE.md` §9. Edit only the sections tagged with your owner letter.
> Every step = a command you can copy + one line saying what it does.
> Commands below are the **planned** ones; each owner verifies and fixes them as they build.

---

## 1. Prerequisites  [Owner: both]

| Tool | Version | Check with |
|---|---|---|
| Git | any | `git --version` |
| Python | 3.11+ | `python3 --version` |
| Flutter | stable (3.x) | `flutter doctor` |
| Android emulator (tablet profile) or Android tablet | API 30+ | `flutter devices` |
| Sarvam AI API key | — | dashboard.sarvam.ai |
| LLM API key | — | your provider |

## 2. First-time setup  [Owner: both]

```bash
git clone <repo-url> rebase && cd rebase      # get the code
cp .env.example .env                           # create your secrets file, then fill in the keys
echo "I am Person A (AI + UI)" > CLAUDE.local.md   # or "I am Person B (Infra)" — tells Claude Code who you are
```

---

## 3. Backend  [Owner: B]

### 3.1 Install
```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate   # isolated Python env (Windows: .venv\Scripts\activate)
pip install -r requirements.txt -r requirements-ai.txt   # install infra + AI dependencies
```

### 3.2 Seed the database
```bash
python -m app.seed          # wipes and refills backend/rebase.db with demo data
python -m app.ai.train_estimator   # trains the time-estimation model on the seeded history (see section 5)
```

### 3.3 Run
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000   # API + simulator on port 8000
```
Open http://localhost:8000/docs to see and try every endpoint.

### 3.4 Test
```bash
pytest -q                   # runs all backend tests (tests/infra = B, tests/ai = A)
```

### 3.5 Common errors  [Owner: B]
| Error | Fix |
|---|---|
| _(fill in as you hit them)_ | |

---

## 4. App  [Owner: B]  (A adds UI-specific errors to 4.5)

### 4.1 Install
```bash
cd app
flutter pub get             # install Dart packages
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
flutter test                # widget/unit tests
```

### 4.5 Common errors  [Owner: both — add rows only]
| Error | Fix |
|---|---|
| App can't reach backend on emulator | Use `10.0.2.2`, not `localhost` |
| Cleartext HTTP blocked on Android | Add `android:usesCleartextTraffic="true"` to AndroidManifest (demo only) |
| _(fill in as you hit them)_ | |

---

## 5. AI services  [Owner: A]

### 5.1 Keys
Fill `SARVAM_API_KEY`, `LLM_PROVIDER`, `LLM_API_KEY`, `LLM_MODEL` in `.env`. Without them, voice/assistant return a clear 503 and everything else still works.

### 5.2 Train the estimator
```bash
cd backend && python -m app.ai.train_estimator   # re-run after every re-seed; writes data/models/estimator.joblib
```

### 5.3 Quick checks
```bash
curl -X POST localhost:8000/assistant/ask -H "Content-Type: application/json" \
  -d '{"machine_id":"mc_001","question":"How do I switch to power mode?","lang":"hi-IN"}'   # Q&A works
curl -X POST localhost:8000/voice/tts -H "Content-Type: application/json" \
  -d '{"text":"नमस्ते","lang":"hi-IN"}' --output test.wav                                   # Sarvam TTS works
```

### 5.4 Common errors
| Error | Fix |
|---|---|
| _(fill in as you hit them)_ | |

## 6. Run the full stack  [Owner: both]

1. Terminal 1: backend (3.3).
2. Terminal 2: app against real backend (4.3).
3. Log in, start a session, then trigger scenarios (section 7).

## 7. Demo scenario triggers  [Owner: B]

```bash
curl -X POST localhost:8000/sim/scenario -H "Content-Type: application/json" \
  -d '{"session_id":"<ses_id>","event":"drowsiness"}'     # fires a drowsiness alert on the tablet
```
Events: `normal`, `seatbelt_off`, `drowsiness`, `distraction`, `operator_absent`, `proximity`, `excessive_idle`, `overheat`, `overload`, `unsafe_operation`.
Or use Swagger: `/docs` → `POST /sim/scenario`.

## 8. Fresh-clone check  [Owner: both — B leads at M5]

- [ ] Followed sections 2–6 in a new folder, no step failed
- [ ] Mock mode works with backend off
- [ ] All demo scenarios in `docs/DEMO.md` work
