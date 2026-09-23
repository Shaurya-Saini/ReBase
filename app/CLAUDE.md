# app/CLAUDE.md — shared Flutter guide (A: UI + edge · B: data layer + Training Hub)

Read the root `CLAUDE.md` first. The Flutter app is split by folder:

| Path | Owner | Contains |
|---|---|---|
| `pubspec.yaml` | B | A edits only inside the `# >>> A deps` … `# <<< A deps` block |
| `lib/main.dart` | B | `ProviderScope` + `MaterialApp.router(theme: AppTheme.dark(), routerConfig: buildRouter())` |
| `lib/core/` | B | `config.dart`, `models/`, `api/api_client.dart`, `api/mock_api_client.dart`, `api/http_api_client.dart`, `api/ws_client.dart` |
| `assets/mock/` | B | fixtures copied from `CONTRACT.md` §4 |
| `lib/features/training/` | B | Training Hub: module steps, video links, quiz, complete, `training_strings.dart` |
| `lib/ui/` | A | `theme.dart`, `router.dart`, `widgets/` (BigButton, StatusCard, AlertBanner) |
| `lib/l10n/` + `l10n.yaml` | A | `app_en.arb`, `app_hi.arb`, `app_ta.arb` (`app_te.arb` = stretch) |
| `lib/edge/` | A | ML Kit CV, telemetry rule engine, alert dispatch (posts to E18) |
| `lib/features/<others>/` | A | login, mode_switch, dashboard, job, session/pre_start, session/briefing, session/live, assistant, voice |
| `test/core/`, `test/features/training/` | B | |
| `test/features/<others>/`, `test/edge/` | A | |

Create the project at M0 (B): `flutter create app --org com.rebase --platforms android`

## M0 stubs (so nobody waits)
- **B:** `ApiClient` with every method from `CONTRACT.md` §6.1 (incl. `postAlert`, `ackAlert`, `tts`, `translate`), `MockApiClient` returning fixtures, `apiClientProvider`, `telemetryStreamProvider`, all model classes (incl. `AlertCreate`, `Telemetry`; can start as thin `fromJson` wrappers), placeholder `TrainingHubScreen`.
- **A:** `AppTheme.dark()`, `buildRouter()` with every route pointing to placeholder screens (the `/training` route points to B's `TrainingHubScreen`), empty shared widgets with final constructors, `edge/` package skeleton.

## Rules for Person A (UI + edge)
- Screens get data **only** through `apiClientProvider` / `telemetryStreamProvider` — never dio or sockets directly.
- All visible text through ARB files. Alert text looked up by alert `type`. Whole app switches language live (en/hi/ta).
- Touch targets ≥ 56dp, dark high contrast, landscape. Alerts: colour + icon + text; sound + vibration for `critical`; one large tap to acknowledge.
- **Edge safety (`lib/edge/`):**
  - Telemetry rules watch `telemetryStreamProvider`; on a threshold breach build an `AlertCreate` (`source: telemetry`) and `apiClientProvider.postAlert(...)` (E18). Debounce per type.
  - Camera CV uses `google_mlkit_face_detection` on the front camera → derive `drowsiness`/`distraction`/`operator_absent` → `AlertCreate` (`source: edge_cv`) → `postAlert` (E18).
- **Voice loop:** hold-to-talk → on-device `speech_to_text` → `api.ask` (E23) → show answer + play with `flutter_tts` (or `api.tts`, E24). Always show the text too.
- Need a new API method or model field? Request it from B (progress file) — don't add it to `core/`.

## Rules for Person B (data layer + Training Hub)
- `ApiClient` / provider signatures are a contract (§6.1) — change only via the protocol.
- `USE_MOCK=true|false` via `--dart-define` switches the whole app between mock and real API.
- The mock must fake the WebSocket telemetry: one `Telemetry` tick every 1 s (so A can build gauges + rules before the backend exists). The mock does **not** emit alerts — the app creates those.
- Training Hub reuses A's theme and `ui/widgets/`; its text lives in `training_strings.dart`, not in A's ARB files.

## Both
- Run `flutter analyze` (and your tests) before every merge to `main`.
