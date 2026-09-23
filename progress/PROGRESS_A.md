# Progress — Person A (Edge AI + UI)

> Only Person A edits this file. Person B reads it.
> Status: ⬜ todo · 🟨 doing · ✅ done (matches CONTRACT, tested, works on real API) · 🟦 done on mock/stub only · ⛔ blocked · ➡️ moved
> Person A writes **no backend code** in v2.0. All screens + on-device intelligence.

**Last updated:** —  **Current milestone:** M0  **Contract version in use:** v2.0

## Tasks

| ID | Task | Endpoints / uses | Milestone | Status | Notes |
|---|---|---|---|---|---|
| A0 | Stubs: `ui/theme.dart` (`AppTheme.dark()`), `ui/router.dart` (`buildRouter()` → every route to a placeholder; `/training` → B's `TrainingHubScreen`), empty shared widgets, `edge/` package skeleton | — | M0 | ⬜ | Blocks B at M0 — do first |
| A1 | Theme + shared widgets (BigButton, StatusCard, AlertBanner) | — | M1 | ⬜ | B's Training Hub reuses these |
| A2 | Login (operator picker, PIN, language picker) + mounted/unmounted mode switch | E2, E3 | M1 | ⬜ | |
| A3 | Unmounted dashboard: today / week / month + hours & rest card | E4, E5 | M1 | ⬜ | |
| A4 | Job detail + estimate screen | E7, E8 | M2 | ⬜ | Reads B's XGBoost estimate |
| A5 | Pre-start checklist screen: fetch, mark items, defect gating UI, complete | E12–E14 | M3 | ⬜ | Checklist content served by B |
| A6 | Briefing screen: display + read-aloud (on-device TTS / E24) | E15, E24 | M3 | ⬜ | |
| A7 | Live session screen: telemetry gauges from WS, alert banner (colour+icon+text+sound/vibration), ack, end summary | W1, E16–E20 | M3 | ⬜ | |
| A8 | On-device telemetry rule engine (`edge/`): seatbelt/proximity/idle/overheat/overload/unsafe → build `AlertCreate` → POST E18; debounce | W1, E18 | M3 | ⬜ | The "rules moved to frontend" part |
| A9 | **Edge CV (ML Kit face detection)**: drowsiness/distraction/absence → `AlertCreate` (`source: edge_cv`) → POST E18 | E18 | M4 | ⬜ | Headline demo moment; real front camera |
| A10 | Voice loop: push-to-talk → on-device STT (`speech_to_text`) → E23 ask → show answer + TTS playback | E23, E24 | M4 | ⬜ | Always show text too |
| A11 | Assistant chat screen (Q&A UI + sources) | E23 | M4 | ⬜ | |
| A12 | l10n: en, hi, ta ARB files incl. alert texts by `type`; full-app language switching | — | M4 | ⬜ | Demo langs en/hi/ta |
| A13 | Tests (`test/features/*`, `test/edge/`) + SETUP "App" / "Edge" sections | — | M5 | ⬜ | |
| A14 | Stretch: noise-robust capture polish, `te-IN`, on-device DSP | — | Stretch | ⬜ | Only after M4 |

## Ready for B
_(e.g. "A0 theme+router pushed @ abc123", "AlertBanner ready for Training Hub")_

## Blockers
_None_

## Requests for partner (B)
_None_

## Session log
| When | Did | Next |
|---|---|---|
