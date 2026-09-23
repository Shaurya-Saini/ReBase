# app/CLAUDE.md — Flutter guide (Person A owns all of `app/` since v2.1)

Read the root `CLAUDE.md` first. Since v2.1 (DECISIONS #14) **Person A owns the entire Flutter app**; Person B owns only the backend and has no Flutter toolchain.

| Path | Owner | Contains |
|---|---|---|
| `pubspec.yaml` | A | all deps (no blocks needed) + `flutter: generate: true` for l10n |
| `lib/main.dart` | A | `ProviderScope` + `MaterialApp.router(theme: AppTheme.dark(), routerConfig: buildRouter())` |
| `lib/core/` | A | `config.dart`, `models/` (+ `models.dart` barrel), `api/api_client.dart`, `api/mock_api_client.dart`, `api/http_api_client.dart`, `api/ws_client.dart` |
| `assets/mock/` | A | fixtures copied from `CONTRACT.md` §4 |
| `lib/features/training/` | A | Training Hub: module steps, video links, quiz, complete (content from B's E26/E27) |
| `lib/ui/` | A | `theme.dart`, `router.dart`, `widgets/` (BigButton, StatusCard, AlertBanner) |
| `lib/l10n/` + `l10n.yaml` | A | `app_en.arb`, `app_hi.arb`, `app_ta.arb` (`app_te.arb` = stretch) |
| `lib/edge/` | A | ML Kit CV, telemetry rule engine, alert dispatch (posts to E18) |
| `lib/features/<others>/` | A | login, mode_switch, dashboard, job, session/pre_start, session/briefing, session/live, assistant, voice |
| `test/` | A | all app tests |

Create the project (A): `flutter create app --org com.rebase --platforms android` (package name `app`, matching existing `package:app/...` imports).

## M0 stubs (A)
- `ApiClient` with every method from `CONTRACT.md` §6.1 (incl. `postAlert`, `ackAlert`, `tts`, `translate`), `MockApiClient` returning fixtures, `apiClientProvider`, `telemetryStreamProvider`, all model classes (incl. `AlertCreate`, `Telemetry`), placeholder `TrainingHubScreen`.
- `AppTheme.dark()`, `buildRouter()` with every route pointing to placeholder screens, shared widgets, `edge/` package skeleton.

## Rules for Person A (UI + edge)
- Screens get data **only** through `apiClientProvider` / `telemetryStreamProvider` — never dio or sockets directly.
- All visible text through ARB files. Alert text looked up by alert `type`. Whole app switches language live (en/hi/ta).
- Touch targets ≥ 56dp, dark high contrast, landscape. Alerts: colour + icon + text; sound + vibration for `critical`; one large tap to acknowledge.
- **Edge safety (`lib/edge/`):**
  - Telemetry rules watch `telemetryStreamProvider`; on a threshold breach build an `AlertCreate` (`source: telemetry`) and `apiClientProvider.postAlert(...)` (E18). Debounce per type.
  - Camera CV uses `google_mlkit_face_detection` on the front camera → derive `drowsiness`/`distraction`/`operator_absent` → `AlertCreate` (`source: edge_cv`) → `postAlert` (E18).
- **Voice loop:** hold-to-talk → on-device `speech_to_text` → `api.ask` (E23) → show answer + play with `flutter_tts` (or `api.tts`, E24). Always show the text too.
- Need a new **endpoint or response field**? Request it from B (progress file) via the contract protocol. `core/` itself is yours.

## Data layer rules (A, formerly B)
- `USE_MOCK=true|false` via `--dart-define` switches the whole app between mock and real API.
- The mock must fake the WebSocket telemetry: one `Telemetry` tick every 1 s. The mock does **not** emit alerts — the app creates those.
- Models must match `CONTRACT.md` §4 JSON exactly (snake_case). Backend shape questions → B's progress file / Swagger `/docs`.

## Checks
- Run `flutter analyze` (and your tests) before every merge to `main`.
