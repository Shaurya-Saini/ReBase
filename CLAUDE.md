# ReBase — CLAUDE.md (shared, read fully at the start of every session)

ReBase is an intelligent **Operator Tablet** for construction/mining equipment operators (excavators, loaders, drill rigs, dump trucks).
This is a **hackathon build (1–3 days)** by **two developers**, each running their own Claude Code on the same repo.
The #1 goal of this file: both people move fast **in parallel without touching each other's work**.

**Architecture is v2.0 (edge); ownership split v2.1 (A = whole Flutter app, B = whole backend).** Contract is `CONTRACT.md` v2.1. If anything below disagrees with `CONTRACT.md`, the contract wins.

---

## 0. Identify who you are working with (do this first)

Each developer creates a gitignored file `CLAUDE.local.md` at the repo root containing exactly one line:

```
I am Person A (Edge AI + UI)      ← or →      I am Person B (Infra + Backend AI)
```

- If `CLAUDE.local.md` is missing, **ask the human "Are you Person A or Person B?" before doing anything else.**
- Every rule below that says "you" means the person named in `CLAUDE.local.md`.

---

## 1. The product (short)

| Mode | State | What the tablet does |
|---|---|---|
| **Mounted** (docked to machine) | Before session | Identify machine → pre-start checklist (co-pilot style, logged) → operational briefing |
| | During session | Live simulated telemetry, **on-device safety detection** (camera CV: drowsiness/distraction/absence; rules: seatbelt/proximity/idling/overheat/overload/unsafe), incident log, manual-based Q&A assistant |
| **Unmounted** (personal time) | — | Daily/weekly/monthly assignments, job + project time estimates, hours worked and rest status, Training Hub (30–45 min pre-shift recap) |

**Super points (the demo must show all three):** multilingual UI + voice (en/hi/ta, switchable live), voice assistant in the operator's first language (on-device STT → RAG answer → TTS), Training Hub + in-session assistant, and the standout — **real on-device computer-vision safety alerts**.

**The v2.0 split of "smart":**
- **On the tablet (A):** real computer vision (Google ML Kit face detection) for operator-state alerts, plus a threshold **rule engine** over streamed telemetry. On-device STT. This is the "edge" story.
- **On the backend (B):** the **simulator** invents machine sensor data and streams it; **RAG + vector DB** serves checklists and the manual Q&A assistant; the **LLM** writes briefings; **XGBoost** predicts job time; Sarvam does TTS + translate.

Machine sensors are **simulated** by the backend. The camera CV is **real**, running on the tablet's front camera. There is **no offline mode in the demo** (it's a proof of application, not the shipped product).

---

## 2. Who does what

| | **Person A — Edge AI + UI** | **Person B — Infra + Backend AI** |
|---|---|---|
| In one line | **The entire Flutter app**: everything the operator *sees* + everything intelligent that runs *on the tablet* | **The entire backend**: everything that *stores, simulates, moves and serves* data, plus all backend AI and Training Hub content |
| Backend | **None** | FastAPI, SQLite DB, models, seed, all endpoints, sessions + checklist gating + fatigue gate, **simulator + WebSocket**, **RAG (checklists + Q&A)**, briefing (LLM), **XGBoost estimator**, Sarvam proxy (TTS + translate), training content + endpoints |
| Flutter app | **All of it** (v2.1): project setup, `pubspec.yaml`, `main.dart`, data models, API client (mock + real), WebSocket client, all screens **incl. Training Hub**, theme, navigation, shared widgets, translations (l10n) + language switching, voice loop (on-device STT + TTS), **edge CV (ML Kit)**, **on-device telemetry rule engine**, alert posting | **None** (B has no Flutter toolchain — see DECISIONS #14) |

---

## 3. Tech stack (fixed — do not change without a DECISIONS.md entry agreed by both)

| Layer | Choice | Owner |
|---|---|---|
| Tablet app | Flutter (Android tablet, landscape), Riverpod, go_router, dio, web_socket_channel | A |
| Backend | Python 3.11+, FastAPI, SQLModel + SQLite | B |
| Live data | Backend **simulator** → WebSocket → app (telemetry only) | B |
| **Edge CV** | **Google ML Kit Face Detection** (`google_mlkit_face_detection`), on-device, pretrained — no training/quantization | A |
| **On-device STT** | `speech_to_text` plugin (push-to-talk) | A |
| **On-device TTS** | `flutter_tts` (default, offline); backend Sarvam TTS as optional upgrade | A (app) / B (proxy) |
| Telemetry rule engine | Plain Dart thresholds on the WS stream (runs on device) | A |
| **RAG / Q&A + checklists** | Vector DB (**ChromaDB**) + `sentence-transformers` embeddings over markdown manuals + checklist content + LLM | B |
| **Estimation model** | **XGBoost**, trained on seeded job history | B |
| Voice + translation | **Sarvam AI** (TTS + translate), called **only from the backend**. Prefer free/on-device where quality allows | B |
| LLM | Provider set by `LLM_PROVIDER` in `.env` (briefing + Q&A) | B |

**Translation strategy (decided):** static UI text = precompiled **ARB files** (offline, free, A). Dynamic AI text (briefing, Q&A) = **LLM answers directly in the target language** (B); Sarvam `/translate` is a fallback only. This keeps Sarvam optional.

---

## 4. Repo layout and ownership

```
rebase/
├── CLAUDE.md                     SHARED  – edit only when both agree
├── CLAUDE.local.md               PERSONAL – gitignored
├── CONTRACT.md                   SHARED  – API + internal code contract (change rules: §6 below)
├── SETUP.md                      SHARED  – edit only sections tagged with your letter
├── .env.example                  B
├── docs/DECISIONS.md             SHARED  – append-only
├── docs/DEMO.md                  SHARED  – finalized together at M5
├── progress/PROGRESS_A.md        A only
├── progress/PROGRESS_B.md        B only
│
├── backend/                      B (entirely)  – see backend/CLAUDE.md
│   ├── requirements.txt          B  (fastapi, uvicorn, sqlmodel, xgboost, chromadb, sentence-transformers, pyyaml, pytest, httpx, python-multipart)
│   ├── app/                      B  (main.py, config, db, models, seed, routers/, services/, simulator/, ai/)
│   │   └── ai/                   B  – RAG, estimator, briefing, Sarvam proxy – see backend/app/ai/CLAUDE.md
│   ├── data/training/            B
│   ├── data/checklists/          B  (checklist content, ingested by RAG)
│   ├── data/manuals/             B  (synthetic manuals, embedded in the vector DB)
│   ├── data/models/              B  (XGBoost model + Chroma store, gitignored)
│   └── tests/                    B
│
└── app/                          A (entirely, since v2.1)  – see app/CLAUDE.md
    ├── pubspec.yaml              A
    ├── assets/mock/              A  (fixtures copied from CONTRACT.md §4)
    ├── lib/main.dart             A
    ├── lib/core/                 A  (config, models, api clients, ws client)
    ├── lib/ui/                   A  (theme, router, shared widgets)
    ├── lib/l10n/                 A
    ├── lib/edge/                 A  (ML Kit CV, telemetry rule engine, alert dispatch)
    ├── lib/features/             A  (all features incl. training)
    └── test/                     A
```

Both may **read** everything. Nobody edits a path owned by the other. Person A writes **no backend code**; Person B writes **no Flutter code** (v2.1).

---

## 5. Golden rules (non-negotiable)

1. **Only edit paths you own** (§4). Need something from your partner? Add it under "Requests for partner" in *your own* progress file and tell your human to ping them. Never "quickly fix" their code.
2. **`CONTRACT.md` is the only source of truth** for HTTP endpoints, WebSocket messages **and** the internal Flutter interfaces between the two halves (`CONTRACT.md` §6). If code and contract disagree, the code is wrong.
3. **Build against stubs, not against your partner.** At M0 each person commits stubs for everything the other imports (see `CONTRACT.md` §6). Stubs return the contract example data. Replace the inside later — never change the signature without the contract protocol.
4. **Shared files with blocks:** only edit inside your own marked block. (Since v2.1 `pubspec.yaml` is entirely A's — no blocks needed.)
5. **Small commits, pull often.** `git pull --rebase` before starting any task and before every push.
6. **No secrets in git.** Keys live in `.env` (gitignored).
7. **Demo-first.** Every feature must be triggerable on demand in the demo.
8. **New dependency = one line in `docs/DECISIONS.md`.** B adds Python deps to `requirements.txt`; A adds Flutter deps to `pubspec.yaml`.
9. **When unsure about scope, pick the simpler option** and log it. Do not stall.

---

## 6. Contract change protocol

1. Proposer describes the change to their human, who confirms with the partner (a chat message is enough).
2. Proposer edits `CONTRACT.md` in a **separate commit** `contract: <what changed>` and adds a change-log row (bump version).
3. **Additive** changes (new optional field, new endpoint, new method) may go in right away. **Breaking** changes (rename, remove, type/signature change) need the partner's explicit OK first.
4. After pulling a contract change, each side updates its own code in its own paths.

---

## 7. Session routine (Claude Code must follow this)

**At session start**
1. Read `CLAUDE.local.md` → know if you are A or B.
2. `git pull --rebase`.
3. Read `CONTRACT.md`, your own progress file, and your partner's (read-only — look for "Requests for partner" addressed to you and newly ✅ items you can integrate).
4. Read the sub-folder guides for the paths you will touch:
   - A: `app/CLAUDE.md`
   - B: `backend/CLAUDE.md`, `backend/app/ai/CLAUDE.md`
5. Tell the human: current milestone, next task ID, and any requests waiting.

**During work**
- One task ID at a time; mark it 🟨 when starting.
- Run tests / `flutter analyze` before committing.
- Commit message format: `A7: live session screen` / `B10: RAG checklist serving`.

**At session end (or every ~2 hours)**
1. Update your progress file (statuses, "Last updated", blockers, requests).
2. If any run/test command, port, env var or seed data changed, update your sections of `SETUP.md`.
3. Commit and push.

---

## 8. Git workflow

- `main` must always run.
- Branches: `a/<task-id>-<short-name>`, `b/<task-id>-<short-name>`.
- Merge your own branch into `main` once it runs (ownership rules prevent conflicts).
- Contract edits: branch `contract/<short-name>`, merged right after partner OK.
- Merge conflict in a file you do not own → **stop and ask the human**; an ownership rule was broken.

---

## 9. Milestones and sync points

At every milestone both stop, pull `main`, run the full stack together, and update progress files.

| Milestone | Target (~36h build) | Done when |
|---|---|---|
| **M0 – Kickoff** | Hour 0–1, together | `CONTRACT.md` frozen. **B:** backend skeleton, DB models (incl. `JobLog`), `get_db`, all routers stubbed returning §4 examples. **A:** Flutter project, `pubspec.yaml`, `main.dart`, `core/` providers + `ApiClient`/`MockApiClient` + `telemetryStreamProvider` stubbed, `ui/theme.dart` + `ui/router.dart` + placeholder screens (incl. Training Hub), shared widgets, `edge/` package skeleton. Both `CLAUDE.local.md` created |
| **M1 – Standalone** | ~Hour 8 | B: core API + seed work (Swagger-testable). A: mock API client + fake telemetry stream + all main screens navigable on mock data |
| **M2 – Unmounted E2E** | ~Hour 14 | App on real backend: login → assignments → estimate (real XGBoost) → rest status |
| **M3 – Mounted E2E** | ~Hour 22 | Start session → checklist (backend) → briefing → live telemetry → **on-device telemetry-rule alert** → ack → end. Alerts logged via E18 |
| **M4 – Super points** | ~Hour 30 | **Real camera CV alert (ML Kit)** live; voice Q&A (on-device STT → RAG answer → TTS) in ≥2 languages; multilingual UI switching (en/hi/ta); Training Hub with quiz |
| **M5 – Freeze + demo** | Last 4–6 hours | Bug fixes only, `SETUP.md` tested from a fresh clone, `DEMO.md` rehearsed twice |

**Workload note (v2.1):** the split is now clean by toolchain: A = the whole Flutter app, B = the whole backend. B has no Flutter toolchain, so B verifies A's integration via Swagger `/docs`, `curl`, and pytest, and publishes exact JSON shapes (the §4 examples) for A's models/mocks. Moving a task = both agree, both progress files updated, DECISIONS.md line, and the path ownership change noted in §4.

---

## 10. SETUP.md — instructions to Claude Code

`SETUP.md` must let a person who has never seen the repo clone it and run the demo in under 15 minutes.

- Keep the existing section structure. Edit only sections tagged `[Owner: A]` / `[Owner: B]` matching you. `[Owner: both]` sections change only at M0 and M5.
- Every step = a **copy-pasteable command** + **one plain-language line** saying what it does.
- Update it **in the same commit** as any change to install/run/test commands, ports, env vars, seed data, or model-training steps.
- At M5, B follows `SETUP.md` from a fresh clone in a clean folder; A fixes app/edge failures, B fixes the rest.

---

## 11. Domain notes (so details are right)

- **Seed data (B):** 4 machine types (`excavator`, `wheel_loader`, `drill_rig`, `dump_truck`), generic models (no brands), ~5 operators with different languages and experience, ~8 jobs across 2 projects, and **~60 past job logs** (`JobLog`) with varied weather/experience so B's XGBoost estimator has something to learn from.
- **Checklists (B, RAG/content):** structured after MSHA 30 CFR 56.14100 (pre-shift examination of mobile equipment), ISO 20474 (earth-moving machinery safety), and typical OEM daily walk-around checks. Stored as structured content, served via E12. UI says **"based on"**, never "certified".
- **Critical defect rule (B enforces at E14):** an item with `critical: true` and status `defect` blocks session start.
- **Fatigue / rest rules (B, at E10):** configurable defaults (max 12h per shift, min 10h rest between shifts, max 60h per 7 days) — placeholders inspired by aviation duty-time rules, not legal limits.
- **Manuals (B):** short synthetic markdown manuals for the generic machines, embedded in the vector DB (don't copy real OEM manuals).
- **Edge CV (A):** ML Kit gives eye-open probability + head Euler angles → derive `drowsiness` (eyes closed > ~2 s), `distraction` (head turned away), `operator_absent` (no face). Runs on the tablet's real front camera. No model training needed.
- **Telemetry rules (A):** thresholds on the WS stream (seatbelt false, proximity_m low, idle_seconds high, hydraulic_temp_c high, load_pct high, unsafe speed+load combos). Each alert debounced (fires once per occurrence), POSTed to E18.
- **Languages:** demo = `en-IN`, `hi-IN`, `ta-IN`. `te-IN` is stretch.
- **Tablet UX (A):** glove-friendly (touch targets ≥ 56dp), dark high-contrast, landscape. Alerts = colour + icon + text + sound/vibration, never colour alone. The Training Hub (A) uses the same theme and shared widgets; its content comes from B's E26/E27.
- **Alert text** is localized in the app by alert `type` (A). Backend/stored `message` is English, for logs.

---

## 12. Scope reality check (be honest in the pitch)

| Feature | Real in demo | Simulated / stretch |
|---|---|---|
| **Operator CV alerts** | **Real** on-device ML Kit face detection on the tablet camera | Full driver-monitoring robustness is stretch |
| Machine data, proximity, seatbelt sensor | — | Simulated by backend; `POST /sim/scenario` steers values so on-device rules fire |
| Estimation (XGBoost) | Model trained on seeded history, real inference | Seed history is synthetic, so accuracy numbers mean little — say so |
| Offline operation | — | Not shown; described as the real-product design (this is a proof of application) |
| Noise cancellation | Push-to-talk + on-device STT | On-device DSP noise suppression is real-product only; ANC hearing protection is a hardware assumption |
| Checklists / Q&A from standards & manuals | RAG structure + logging real | Not a certified compliance tool |
| Manager portal | Assignments via Swagger `/docs` or seed | No manager UI |
| Training Hub | Curated static content + quiz | "Heavy video synthesis" is real-product; revisit at project end |

---

## 13. Definition of done (per task)

- Matches `CONTRACT.md` exactly (HTTP, WS, and internal Flutter interfaces).
- Runs from `main` with the commands in `SETUP.md`.
- Backend: at least one pytest per endpoint/service in `tests/`. App: `flutter analyze` clean, works on mock and real API.
- Progress file updated.
