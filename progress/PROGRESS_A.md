# Progress — Person A (Edge AI + UI)

> Only Person A edits this file. Person B reads it.
> Status: ⬜ todo · 🟨 doing · ✅ done (matches CONTRACT, tested, works on real API) · 🟦 done on mock/stub only · ⛔ blocked · ➡️ moved
> Person A writes **no backend code** in v2.0. All screens + on-device intelligence.

**Last updated:** 2026-09-23 (A0 authored; A8 rule engine done + verified)  **Current milestone:** M0  **Contract version in use:** v2.0

## Tasks

| ID | Task | Endpoints / uses | Milestone | Status | Notes |
|---|---|---|---|---|---|
| A0 | Stubs: `ui/theme.dart` (`AppTheme.dark()`), `ui/router.dart` (`buildRouter()` → every route to a placeholder; `/training` → B's `TrainingHubScreen`), empty shared widgets, `edge/` package skeleton | — | M0 | 🟦 | Files authored; `flutter analyze` pending B0 (project/pubspec/`TrainingHubScreen` stub). See Requests for B |
| A1 | Theme + shared widgets (BigButton, StatusCard, AlertBanner) | — | M1 | ⬜ | B's Training Hub reuses these |
| A2 | Login (operator picker, PIN, language picker) + mounted/unmounted mode switch | E2, E3 | M1 | ⬜ | |
| A3 | Unmounted dashboard: today / week / month + hours & rest card | E4, E5 | M1 | ⬜ | |
| A4 | Job detail + estimate screen | E7, E8 | M2 | ⬜ | Reads B's XGBoost estimate |
| A5 | Pre-start checklist screen: fetch, mark items, defect gating UI, complete | E12–E14 | M3 | ⬜ | Checklist content served by B |
| A6 | Briefing screen: display + read-aloud (on-device TTS / E24) | E15, E24 | M3 | ⬜ | |
| A7 | Live session screen: telemetry gauges from WS, alert banner (colour+icon+text+sound/vibration), ack, end summary | W1, E16–E20 | M3 | ⬜ | |
| A8 | On-device telemetry rule engine (`edge/`): seatbelt/proximity/idle/overheat/overload/unsafe → build `AlertCreate` → POST E18; debounce | W1, E18 | M3 | 🟦 | Engine logic done + verified (8/8 checks). Pure Dart, edge-triggered + severity escalation. Remaining: swap `AlertDraft`→core `AlertCreate` and wire `postAlert` (needs B0). Test at `test/edge/telemetry_rules_test.dart` |
| A9 | **Edge CV (ML Kit face detection)**: drowsiness/distraction/absence → `AlertCreate` (`source: edge_cv`) → POST E18 | E18 | M4 | 🟨 | Decision logic done + verified (7/7): `cv_decider.dart` (sustained-window timing, latch/re-arm, blink rejection). `cv_monitor.dart` = plugin shell. Remaining: wire `camera`+ML Kit `FaceDetector` frames → `onObservation` (needs project + device) + `postAlert`. Test at `test/edge/cv_decider_test.dart` |
| A10 | Voice loop: push-to-talk → on-device STT (`speech_to_text`) → E23 ask → show answer + TTS playback | E23, E24 | M4 | ⬜ | Always show text too |
| A11 | Assistant chat screen (Q&A UI + sources) | E23 | M4 | ⬜ | |
| A12 | l10n: en, hi, ta ARB files incl. alert texts by `type`; full-app language switching | — | M4 | 🟦 | ARB files done (38 keys × en/hi/ta, JSON + key-parity verified) + `l10n.yaml`. Alert texts keyed by type. Remaining: `flutter gen-l10n` (needs B pubspec `generate: true`) + language-switch provider + wire strings into screens. hi/ta need a native-speaker review pass |
| A13 | Tests (`test/features/*`, `test/edge/`) + SETUP "App" / "Edge" sections | — | M5 | ⬜ | |
| A14 | Stretch: noise-robust capture polish, `te-IN`, on-device DSP | — | Stretch | ⬜ | Only after M4 |

## Ready for B
- **A0 authored** (not yet pushed): `lib/ui/theme.dart` (`AppTheme.dark()`, `severityColor`), `lib/ui/router.dart` (`buildRouter()`), shared widgets `BigButton`/`StatusCard`/`AlertBanner` (ready for your Training Hub), placeholder screens for all A features, `lib/edge/` skeleton.
- Package name assumed **`app`** (from `flutter create app --org com.rebase`). Imports use `package:app/...`. Tell me if you use a different `name:`.

## Blockers
- **B0 needed to compile A0:** no Flutter project yet (`flutter create`, `pubspec.yaml`, `lib/main.dart`, `lib/core/` stubs, and the `TrainingHubScreen` stub at `lib/features/training/training_hub_screen.dart`). My files reference `package:app/features/training/training_hub_screen.dart` per CONTRACT §6.1.

## Requests for partner (B)
1. **pubspec:** add the `# >>> A deps … # <<< A deps` block in `dependencies:` so I can add my deps. A-block deps I need (I'll fill them, just need the markers): `flutter_riverpod`, `go_router`, `google_mlkit_face_detection`, `camera`, `speech_to_text`, `flutter_tts`, `intl`, and `flutter_localizations` (sdk). Also set `flutter: generate: true` for l10n (A12).
2. **Models barrel:** please export a `lib/core/models/models.dart` barrel so `edge/` and screens import one path (§6.1). My edge stubs use a local `AlertDraft` for now and will swap to core `AlertCreate` in A8.
3. **`.gitignore`:** it ignores `*.joblib` but v2.0 uses XGBoost `estimator.json` + a Chroma store — add `backend/data/models/estimator.json` and `backend/data/models/chroma/` (your file, flagging only).
4. Confirm `TrainingHubScreen` constructor matches CONTRACT §6.1: `TrainingHubScreen({required String operatorId, required String machineType})` — my router builds it that way.

## Session log
| When | Did | Next |
|---|---|---|
| 2026-09-23 | A0: authored theme, router, 3 shared widgets, 8 placeholder screens, edge skeleton (rules/CV/dispatch). Blocked on B0 for `flutter analyze`. | Pull once B0 lands → `flutter analyze` → fix imports → push A0. Then A1 (real theme + widgets). |
| 2026-09-23 | A8 (early): implemented full telemetry rule engine in `edge/telemetry_rules.dart` (edge-trigger, debounce, severity escalation, 6 alert types) + `test/edge/telemetry_rules_test.dart`. Verified 8/8 with a standalone `dart run` (no project needed). | Wire engine → `postAlert` (E18) in `alert_dispatch.dart` once B exposes core `AlertCreate`. |
| 2026-09-23 | A12 (content): authored `l10n.yaml` + `app_en/hi/ta.arb` (38 keys each, incl. all 9 alert types by `type`). Validated JSON + key parity across locales. | After B0: `flutter gen-l10n`, add a locale provider for live switching, wire keys into screens. Flag hi/ta for native review. |
| 2026-09-23 | A9 (logic): split the headline CV feature — `cv_decider.dart` (pure-Dart decision logic: sustained-window drowsiness/distraction/absence, latch + re-arm, blink rejection) + `cv_monitor.dart` (ML Kit plugin shell) + `test/edge/cv_decider_test.dart`. Verified 7/7 standalone. | Wire ML Kit `FaceDetector` + front `camera` → `onObservation` on a real device once B0 lands; then `postAlert` (E18). |
