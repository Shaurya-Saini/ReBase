# Progress — Person A (Edge AI + UI)

> Only Person A edits this file. Person B reads it.
> Status: ⬜ todo · 🟨 doing · ✅ done (matches CONTRACT, tested, works on real API) · 🟦 done on mock/stub only · ⛔ blocked · ➡️ moved
> Person A writes **no backend code** in v2.0. All screens + on-device intelligence.

**Last updated:** 2026-09-23 (v2.1 accepted; app scaffolded, analyze clean, tests green)  **Current milestone:** M0→M1  **Contract version in use:** v2.1

## Tasks

| ID | Task | Endpoints / uses | Milestone | Status | Notes |
|---|---|---|---|---|---|
| A0 | Stubs: `ui/theme.dart` (`AppTheme.dark()`), `ui/router.dart` (`buildRouter()` → every route to a placeholder; `/training` → `TrainingHubScreen`), shared widgets, `edge/` package skeleton | — | M0 | ✅ | Compiles; `flutter analyze` clean; app runs on scaffold |
| A1 | Theme + shared widgets (BigButton, StatusCard, AlertBanner) | — | M1 | ⬜ | B's Training Hub reuses these |
| A2 | Login (operator picker, PIN, language picker) + mounted/unmounted mode switch | E2, E3 | M1 | 🟦 | Login + live language switch (en/hi/ta) done on mock; widget test. Picking an operator sets their language. Mode-switch folded into flow (dashboard = unmounted; session start = mounted) |
| A3 | Unmounted dashboard: today / week / month + hours & rest card | E4, E5 | M1 | 🟦 | Done on mock: hours + rest StatusCards, day/week/month toggle, assignment cards → job. Widget test |
| A4 | Job detail + estimate screen | E7, E8 | M2 | 🟦 | Done on mock: job detail + estimate (hours, range, factor breakdown, completion) + start-session → pre-start. Widget test |
| A5 | Pre-start checklist screen: fetch, mark items, defect gating UI, complete | E12–E14 | M3 | 🟦 | Done on mock: sections/items, OK/Defect/N-A per item, CRITICAL badges, **critical-defect gate blocks completion** (client + backend), per-item PUT (E13), complete → briefing. Widget tests |
| A6 | Briefing screen: display + read-aloud (on-device TTS / E24) | E15, E24 | M3 | 🟦 | Done on mock: machine/job/estimate + hazards + reminders; **on-device read-aloud** via `flutter_tts` in the operator's language. Widget test |
| A7 | Live session screen: telemetry gauges from WS, alert banner (colour+icon+text+sound/vibration), ack, end summary | W1, E16–E20 | M3 | 🟦 | Done on mock: 8 telemetry gauges (danger-coloured), localized alert banner + haptics/sound on critical, ack, end→summary dialog. Mock-only demo triggers (seatbelt/proximity/overheat/CV). Widget test |
| A8 | On-device telemetry rule engine (`edge/`): seatbelt/proximity/idle/overheat/overload/unsafe → build `AlertCreate` → POST E18; debounce | W1, E18 | M3 | 🟦 | Engine done + verified; now **wired end-to-end** in A7 via `AlertDispatcher` → `postAlert` (E18) on mock. Real-backend post untested (needs B running) |
| A9 | **Edge CV (ML Kit face detection)**: drowsiness/distraction/absence → `AlertCreate` (`source: edge_cv`) → POST E18 | E18 | M4 | 🟨 | Decision logic done + verified (7/7): `cv_decider.dart` (sustained-window timing, latch/re-arm, blink rejection). `cv_monitor.dart` = plugin shell. Remaining: wire `camera`+ML Kit `FaceDetector` frames → `onObservation` (needs project + device) + `postAlert`. Test at `test/edge/cv_decider_test.dart` |
| A10 | Voice loop: push-to-talk → on-device STT (`speech_to_text`) → E23 ask → show answer + TTS playback | E23, E24 | M4 | 🟦 | Wired: hold-to-talk mic → STT fills question → ask → answer read aloud (`flutter_tts`). Text always shown. STT/TTS need a device to exercise; `core/stt.dart` added |
| A11 | Assistant chat screen (Q&A UI + sources) | E23 | M4 | 🟦 | Done on mock: chat bubbles, grounded answer + source, per-answer read-aloud. Widget test (text path) |
| A12 | l10n: en, hi, ta ARB files incl. alert texts by `type`; full-app language switching | — | M4 | 🟦 | ARB files done (38 keys × en/hi/ta, JSON + key-parity verified) + `l10n.yaml`. Alert texts keyed by type. Remaining: `flutter gen-l10n` (needs B pubspec `generate: true`) + language-switch provider + wire strings into screens. hi/ta need a native-speaker review pass |
| A13 | Tests (`test/features/*`, `test/edge/`) + SETUP "App" / "Edge" sections | — | M5 | ⬜ | |
| A14 | Stretch: noise-robust capture polish, `te-IN`, on-device DSP | — | Stretch | ⬜ | Only after M4 |
| A15 | Scaffold Flutter project (`flutter create`), `pubspec.yaml`, `main.dart`, l10n codegen, `core/locale.dart` | — | M0 | ✅ | Done. `flutter pub get` (44 deps), `gen-l10n` (en/hi/ta), `analyze` clean, `flutter test` 10/10. Edge/voice deps deferred to A9/A10 |
| A16 | Data layer: `core/models/*` (per §4) + barrel, `ApiClient`, `MockApiClient` + Dart fixtures, `telemetryStreamProvider`, `apiClientProvider` | §6.1 | M1 | ✅ | 12 model files + barrel; MockApiClient stateful (alert post→list→ack); fake 1 Hz telemetry. `analyze` clean, tests 15/15. Fixtures in Dart (`mock_data.dart`), not assets/mock |
| A17 | `HttpApiClient` (all endpoints incl. binary TTS, alert POST) | §6.1 | M2 | 🟦 | Implemented (dio, 1:1 with §3). **Untested against backend** — verify vs B's stubs (needs backend running) |
| A18 | Training Hub screens (steps, video, quiz, complete, 3 langs) — consumes E26/E27 | E26, E27 | M4 | ⬜ | Adopted from B14; content from B13 |

## Ready for B
- **A0 authored** (not yet pushed): `lib/ui/theme.dart` (`AppTheme.dark()`, `severityColor`), `lib/ui/router.dart` (`buildRouter()`), shared widgets `BigButton`/`StatusCard`/`AlertBanner` (ready for your Training Hub), placeholder screens for all A features, `lib/edge/` skeleton.
- Package name assumed **`app`** (from `flutter create app --org com.rebase`). Imports use `package:app/...`. Tell me if you use a different `name:`.

## Blockers
_None._ v2.1 (DECISIONS #14): I own the whole `app/` and have Flutter installed — self-unblocked. Scaffolding the project myself (A15).

## Requests for partner (B)
- **OK given on the v2.1 re-split** (DECISIONS #14 / CONTRACT v2.1). I now own the entire Flutter app. My old requests 1, 2, 4 are **closed** — they became my own tasks (pubspec/deps, `core/models` barrel, `TrainingHubScreen`).
- (Open) #3: add `backend/data/models/estimator.json` + `backend/data/models/chroma/` to `.gitignore` — B said they'll handle it with B0.

## Session log
| When | Did | Next |
|---|---|---|
| 2026-09-23 | A0: authored theme, router, 3 shared widgets, 8 placeholder screens, edge skeleton (rules/CV/dispatch). Blocked on B0 for `flutter analyze`. | Pull once B0 lands → `flutter analyze` → fix imports → push A0. Then A1 (real theme + widgets). |
| 2026-09-23 | A8 (early): implemented full telemetry rule engine in `edge/telemetry_rules.dart` (edge-trigger, debounce, severity escalation, 6 alert types) + `test/edge/telemetry_rules_test.dart`. Verified 8/8 with a standalone `dart run` (no project needed). | Wire engine → `postAlert` (E18) in `alert_dispatch.dart` once B exposes core `AlertCreate`. |
| 2026-09-23 | A12 (content): authored `l10n.yaml` + `app_en/hi/ta.arb` (38 keys each, incl. all 9 alert types by `type`). Validated JSON + key parity across locales. | After B0: `flutter gen-l10n`, add a locale provider for live switching, wire keys into screens. Flag hi/ta for native review. |
| 2026-09-23 | A9 (logic): split the headline CV feature — `cv_decider.dart` (pure-Dart decision logic: sustained-window drowsiness/distraction/absence, latch + re-arm, blink rejection) + `cv_monitor.dart` (ML Kit plugin shell) + `test/edge/cv_decider_test.dart`. Verified 7/7 standalone. | Wire ML Kit `FaceDetector` + front `camera` → `onObservation` on a real device once B0 lands; then `postAlert` (E18). |
| 2026-09-23 | v2.1 accepted; **A15** scaffolded the real Flutter app (pubspec, main, l10n gen). **A16** built the whole data layer (12 models + barrel, `ApiClient`, tested `MockApiClient`, fake telemetry stream, `apiClientProvider`). **A17** `HttpApiClient` implemented. `analyze` clean, `flutter test` 15/15. | Wire screens onto the data layer: A2 login (operator picker + PIN + language), A3 dashboard, then A7 live screen (telemetry + edge alerts). Verify A17 against B's running backend later. |
| 2026-09-23 | Merged B's seed+fatigue commits (green). **A2** login (operator picker + PIN + live en/hi/ta switch) and **A3** dashboard (hours/rest cards + day/week/month + assignment→job) wired to the data layer + `data_providers.dart`. Widget tests for both. `analyze` clean, `flutter test` 18/18. | A4 job+estimate screen, then A7 live session (telemetry gauges + wire edge rule engine → `postAlert`). |
| 2026-09-24 | **A4** job+estimate screen and **A7** live session done on mock. A7 connects it all: telemetry stream → **A8 rule engine** → `AlertDispatcher.postAlert` (E18) → localized banner (haptics/sound) → ack → end summary. `AlertDispatcher` made real; `ui/alert_text.dart` localizes alerts by type; mock-only demo triggers incl. CV. Widget tests for A4 + A7. `analyze` clean, `flutter test` 21/21. | A5 pre-start checklist + A6 briefing; then A9 ML Kit camera wiring on device; verify A17 vs B's running backend. |
| 2026-09-24 | **A5** pre-start checklist (item marking, CRITICAL badges, critical-defect gate, complete→briefing) and **A6** briefing (summaries + hazards/reminders + on-device read-aloud via `flutter_tts`). Added `flutter_tts` dep, `core/tts.dart`, `core/lang.dart`, checklist/briefing providers. Widget tests. Whole **mounted flow now real on mock**. `analyze` clean, `flutter test` 24/24. | A9 ML Kit camera on device; A10/A11 voice assistant loop; A18 Training Hub; verify A17 vs B's real backend. |
| 2026-09-24 | **A11** assistant chat (bubbles, grounded answer + source, read-aloud) + **A10** voice loop (hold-to-talk → on-device STT → ask → TTS). Added `speech_to_text` dep + `core/stt.dart` + `sttLocaleId`. Widget test (text path). `analyze` clean, `flutter test` 25/25. | A9 ML Kit camera wiring on device (CV logic already tested); A18 Training Hub (later); verify A17 vs B's real backend. |
