# ReBase — CLAUDE.md (shared, read fully at the start of every session)

ReBase is an intelligent **Operator Tablet** for construction/mining equipment operators (excavators, loaders, drill rigs, dump trucks).
This is a **hackathon build (1–3 days)** by **two developers**, each running their own Claude Code on the same repo.
The #1 goal of this file: both people move fast **in parallel without touching each other's work**.

---

## 0. Identify who you are working with (do this first)

Each developer creates a gitignored file `CLAUDE.local.md` at the repo root containing exactly one line:

```
I am Person A (AI + UI)      ← or →      I am Person B (Infra)
```

- If `CLAUDE.local.md` is missing, **ask the human "Are you Person A or Person B?" before doing anything else.**
- Every rule below that says "you" means the person named in `CLAUDE.local.md`.

---

## 1. The product (short)

| Mode | State | What the tablet does |
|---|---|---|
| **Mounted** (docked to machine) | Before session | Identify machine → pre-start checklist (co-pilot style, logged) → operational briefing |
| | During session | Live telemetry, safety alerts (seatbelt, drowsiness, proximity, idling, unsafe operation), incident log, manual-based Q&A assistant |
| **Unmounted** (personal time) | — | Daily/weekly/monthly assignments, job + project time estimates, hours worked and rest status, Training Hub (30–45 min pre-shift recap) |

**Super points (the demo must show all three):** multilingual UI + voice (Sarvam AI), voice assistant in the operator's first language with noisy-environment handling, Training Hub + in-session assistant.

All machine data (sensors, cameras, machine ID) is **simulated** by the backend.

---

## 2. Who does what

| | **Person A — AI + UI** | **Person B — Infra** |
|---|---|---|
| In one line | Everything the operator *sees* and everything that is *intelligent* | Everything that *stores, moves and serves* data, plus the Training Hub end to end |
| Backend | `backend/app/ai/`: Sarvam (speech-to-text, text-to-speech, translate), LLM, manual Q&A, AI estimations + model training, briefing generation, checklist content from standards | FastAPI app, SQLite DB, models, seed data, all core endpoints, sessions + checklist gating, simulator, safety rule engine, WebSocket, fatigue/rest logic, training content + endpoints |
| Flutter app | All screens except Training Hub, theme, navigation, shared widgets, translations (l10n), voice recording/playback | Project setup, data models, API client (mock + real), WebSocket client, Training Hub screens |

---

## 3. Tech stack (fixed — do not change without a DECISIONS.md entry agreed by both)

| Layer | Choice | Owner |
|---|---|---|
| Tablet app | Flutter (Android tablet, landscape), Riverpod, go_router, dio, web_socket_channel | Setup/data: B · Screens: A |
| Backend | Python 3.11+, FastAPI, SQLModel + SQLite | B |
| Live data | WebSocket backend → app | B |
| Simulator | Python module inside the backend process | B |
| Manual Q&A | BM25 search (`rank_bm25`) over markdown manuals + LLM | A |
| Estimation model | scikit-learn, trained on seeded job history | A |
| Voice + translation | Sarvam AI, called **only from the backend** (keys never ship in the app) | A |
| LLM | Provider set by `LLM_PROVIDER` in `.env` | A |

---

## 4. Repo layout and ownership

```
rebase/
├── CLAUDE.md                     SHARED  – edit only when both agree
├── CLAUDE.local.md               PERSONAL – gitignored
├── CONTRACT.md                   SHARED  – API + internal code contract (change rules: §6 below)
├── SETUP.md                      SHARED  – edit only sections tagged with your letter
├── .env.example                  B (A asks B to add keys)
├── docs/DECISIONS.md             SHARED  – append-only
├── docs/DEMO.md                  SHARED  – finalized together at M5
├── progress/PROGRESS_A.md        A only
├── progress/PROGRESS_B.md        B only
│
├── backend/                      B  – see backend/CLAUDE.md
│   ├── requirements.txt          B
│   ├── requirements-ai.txt       A
│   ├── app/                      B  (main.py, config, db, models, seed, routers/, services/, simulator/)
│   │   └── ai/                   A  – see backend/app/ai/CLAUDE.md
│   ├── data/training/            B
│   ├── data/checklists/          A
│   ├── data/manuals/             A
│   ├── data/models/              A  (trained model files, gitignored)
│   ├── tests/infra/              B
│   └── tests/ai/                 A
│
└── app/                          see app/CLAUDE.md
    ├── pubspec.yaml              B (A edits only inside the "# >>> A deps" block)
    ├── assets/mock/              B
    ├── lib/main.dart             B
    ├── lib/core/                 B  (config, models, api clients, ws client)
    ├── lib/ui/                   A  (theme, router, shared widgets)
    ├── lib/l10n/                 A
    ├── lib/features/training/    B
    ├── lib/features/<all other>/ A
    ├── test/core/ + test/features/training/   B
    └── test/features/<others>/   A
```

Both may **read** everything. Nobody edits a path owned by the other.

---

## 5. Golden rules (non-negotiable)

1. **Only edit paths you own** (§4). Need something from your partner? Add it under "Requests for partner" in *your own* progress file and tell your human to ping them. Never "quickly fix" their code.
2. **`CONTRACT.md` is the only source of truth** for HTTP endpoints, WebSocket messages **and** the internal code interfaces between the two halves (Python functions and Flutter providers, `CONTRACT.md` §6). If code and contract disagree, the code is wrong.
3. **Build against stubs, not against your partner.** At M0 each person commits stubs for everything the other imports (see `CONTRACT.md` §6). Stubs return the contract example data. Replace the inside later — never change the signature without the contract protocol.
4. **Shared files with blocks** (`pubspec.yaml`): only edit inside your own marked block. Git merges separate blocks automatically.
5. **Small commits, pull often.** `git pull --rebase` before starting any task and before every push.
6. **No secrets in git.** Keys live in `.env` (gitignored).
7. **Demo-first.** Every feature must be triggerable on demand in the demo.
8. **New dependency = one line in `docs/DECISIONS.md`.** A adds Python deps to `requirements-ai.txt`, Flutter deps inside the A block of `pubspec.yaml`.
9. **When unsure about scope, pick the simpler option** and log it. Do not stall.

---

## 6. Contract change protocol

1. Proposer describes the change to their human, who confirms with the partner (a chat message is enough).
2. Proposer edits `CONTRACT.md` in a **separate commit** `contract: <what changed>` and adds a change-log row (bump version).
3. **Additive** changes (new optional field, new endpoint, new function) may go in right away. **Breaking** changes (rename, remove, type/signature change) need the partner's explicit OK first.
4. After pulling a contract change, each side updates its own code in its own paths.

---

## 7. Session routine (Claude Code must follow this)

**At session start**
1. Read `CLAUDE.local.md` → know if you are A or B.
2. `git pull --rebase`.
3. Read `CONTRACT.md`, your own progress file, and your partner's (read-only — look for "Requests for partner" addressed to you and newly ✅ items you can integrate).
4. Read the sub-folder guides for the paths you will touch:
   - A: `backend/app/ai/CLAUDE.md`, `app/CLAUDE.md`
   - B: `backend/CLAUDE.md`, `app/CLAUDE.md`
5. Tell the human: current milestone, next task ID, and any requests waiting.

**During work**
- One task ID at a time; mark it 🟨 when starting.
- Run tests / `flutter analyze` before committing.
- Commit message format: `A9: BM25 manual search` / `B7: simulator scenarios`.

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
| **M0 – Kickoff** | Hour 0–1, together | `CONTRACT.md` frozen. **B:** backend skeleton, DB models, `get_db`, Flutter project, `main.dart`, core providers stubbed. **A:** `ai/` router + `ai/api.py` stubs, `ui/theme.dart` + `ui/router.dart` stubs. Both `CLAUDE.local.md` created |
| **M1 – Standalone** | ~Hour 8 | B: core API + seed + mock API client work. A: all main screens navigable on mock data, checklist content ready |
| **M2 – Unmounted E2E** | ~Hour 14 | App on real backend: login → assignments → estimate (real model) → rest status |
| **M3 – Mounted E2E** | ~Hour 22 | Start session → checklist → briefing → live telemetry → alert → ack → end |
| **M4 – Super points** | ~Hour 30 | Voice Q&A in ≥2 Indian languages, multilingual UI, Training Hub with quiz |
| **M5 – Freeze + demo** | Last 4–6 hours | Bug fixes only, `SETUP.md` tested from a fresh clone, `DEMO.md` rehearsed twice |

**Workload note:** A's list is larger. If B finishes a milestone early, the agreed candidates to move to B are, in order: (1) the unmounted dashboard screen, (2) the live-session telemetry gauges. Moving a task = both agree, both progress files updated, DECISIONS.md line, and the path ownership change noted in §4.

---

## 10. SETUP.md — instructions to Claude Code

`SETUP.md` must let a person who has never seen the repo clone it and run the demo in under 15 minutes.

- Keep the existing section structure. Edit only sections tagged `[Owner: A]` / `[Owner: B]` matching you. `[Owner: both]` sections change only at M0 and M5.
- Every step = a **copy-pasteable command** + **one plain-language line** saying what it does.
- Update it **in the same commit** as any change to install/run/test commands, ports, env vars, seed data, or model-training steps.
- At M5, B follows `SETUP.md` from a fresh clone in a clean folder; A fixes AI-section failures, B fixes the rest.

---

## 11. Domain notes (so details are right)

- **Seed data (B):** 4 machine types (`excavator`, `wheel_loader`, `drill_rig`, `dump_truck`), generic models (no brands), ~5 operators with different languages and experience, ~8 jobs across 2 projects, and **~60 past job logs** with varied weather/experience so A's estimator has something to learn from.
- **Checklists (A):** structured after MSHA 30 CFR 56.14100 (pre-shift examination of mobile equipment, defects recorded and fixed before use), ISO 20474 (earth-moving machinery safety), and typical OEM daily walk-around checks. UI says **"based on"**, never "certified".
- **Critical defect rule (B enforces):** an item with `critical: true` and status `defect` blocks session start.
- **Fatigue / rest rules (B):** configurable defaults (max 12h per shift, min 10h rest between shifts, max 60h per 7 days) — placeholders inspired by aviation duty-time rules, not legal limits.
- **Manuals (A):** short synthetic markdown manuals for the generic machines (don't copy real OEM manuals).
- **Languages:** `en-IN`, `hi-IN`, `ta-IN`, `te-IN` minimum.
- **Tablet UX (A):** glove-friendly (touch targets ≥ 56dp), dark high-contrast, landscape. Alerts = colour + icon + text + sound/vibration, never colour alone. B's Training Hub uses A's theme and shared widgets.
- **Alert text** is localized in the app by alert `type` (A). Backend `message` is English, for logs.

---

## 12. Scope reality check (be honest in the pitch)

| Feature | Real in demo | Simulated / stretch |
|---|---|---|
| Machine data, cameras, proximity | — | Simulated; scenario triggers for demo |
| Operator behaviour detection | Alerts + logging real | Detection simulated. Stretch (A): on-device face detection via tablet camera |
| "Model training" | Estimator trained on seeded history | Seed history is synthetic, so accuracy numbers mean little — say so |
| Noise cancellation | Push-to-talk + noise-robust speech-to-text | Hearing protection needs an ANC headset — present as hardware assumption |
| Checklists from standards | Structure + logging real | Not a certified compliance tool |
| Manager portal | Assignments via Swagger `/docs` or seed | No manager UI |

---

## 13. Definition of done (per task)

- Matches `CONTRACT.md` exactly (HTTP and internal interfaces).
- Runs from `main` with the commands in `SETUP.md`.
- Backend: at least one pytest per endpoint/function in your test folder. App: `flutter analyze` clean, works on mock and real API.
- Progress file updated.
