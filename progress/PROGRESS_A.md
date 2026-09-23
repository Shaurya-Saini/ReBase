# Progress — Person A (AI + UI)

> Only Person A edits this file. Person B reads it.
> Status: ⬜ todo · 🟨 doing · ✅ done (matches CONTRACT, tested, works on real API) · 🟦 done on mock/stub only · ⛔ blocked · ➡️ moved

**Last updated:** —  **Current milestone:** M0  **Contract version in use:** v1.1

## Tasks

| ID | Task | Side | Endpoints / uses | Milestone | Status | Notes |
|---|---|---|---|---|---|---|
| A0 | Stubs: `ai/router.py` + `ai/api.py` (contract examples); `ui/theme.dart` + `ui/router.dart` + placeholder screens | Both | — | M0 | ⬜ | Blocks B at M0 — do first |
| A1 | Theme + shared widgets (BigButton, StatusCard, AlertBanner) | App | — | M1 | ⬜ | |
| A2 | Login (operator picker, PIN, language picker) + mode switch | App | E2, E3 | M1 | ⬜ | |
| A3 | Unmounted dashboard: today / week / month + hours & rest card | App | E4, E5 | M1 | ⬜ | Move candidate → B |
| A4 | Checklist YAMLs for 4 machine types (based on MSHA 56.14100 / ISO 20474 / OEM walk-around) + `load_checklist()` | Backend | used by E12 | M1 | ⬜ | |
| A5 | Estimator: train on `JobLog`, fallback formula, E8 + job detail screen | Both | E7, E8 | M2 | ⬜ | Needs B1 seed |
| A6 | Pre-start checklist screen with defect gating | App | E10–E14 | M3 | ⬜ | |
| A7 | Briefing generation (LLM + template fallback) E15 + briefing screen | Both | E15 | M3 | ⬜ | |
| A8 | Live session screen: gauges, alert banner, sound/vibration, ack, end summary | App | W1, E16–E19 | M3 | ⬜ | Gauges = move candidate → B |
| A9 | Synthetic manuals + BM25 + LLM Q&A with sources (E20) + assistant chat screen | Both | E20 | M4 | ⬜ | |
| A10 | Sarvam proxy: STT, TTS, translate (E21, E22) | Backend | E21, E22 | M4 | ⬜ | |
| A11 | Voice loop in app: hold-to-talk → STT → ask → TTS; briefing read-aloud | App | E20–E22 | M4 | ⬜ | |
| A12 | l10n: en, hi, ta, te ARB files, incl. alert texts by type | App | — | M4 | ⬜ | |
| A13 | Tests (`tests/ai`, widget tests) + SETUP "AI services" section | Both | — | M5 | ⬜ | |
| A14 | Stretch: on-device drowsiness check (tablet camera face detection) | App | — | Stretch | ⬜ | Only after M4 |

## Ready for B
_(e.g. "A0 stubs pushed @ abc123", "load_checklist() real for all 4 types")_

## Blockers
_None_

## Requests for partner (B)
_None_

## Session log
| When | Did | Next |
|---|---|---|
