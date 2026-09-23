# app/CLAUDE.md — shared Flutter guide (A: UI · B: data layer + Training Hub)

Read the root `CLAUDE.md` first. The Flutter app is split by folder:

| Path | Owner | Contains |
|---|---|---|
| `pubspec.yaml` | B | A edits only inside the `# >>> A deps` … `# <<< A deps` block |
| `lib/main.dart` | B | `ProviderScope` + `MaterialApp.router(theme: AppTheme.dark(), routerConfig: buildRouter())` |
| `lib/core/` | B | `config.dart`, `models/`, `api/api_client.dart`, `api/mock_api_client.dart`, `api/http_api_client.dart`, `api/ws_client.dart` |
| `assets/mock/` | B | fixtures copied from `CONTRACT.md` §4 |
| `lib/features/training/` | B | Training Hub: module steps, video links, quiz, complete, `training_strings.dart` |
| `lib/ui/` | A | `theme.dart`, `router.dart`, `widgets/` (BigButton, StatusCard, AlertBanner) |
| `lib/l10n/` + `l10n.yaml` | A | `app_en.arb`, `app_hi.arb`, `app_ta.arb`, `app_te.arb` |
| `lib/features/<others>/` | A | login, mode_switch, dashboard, job, session/pre_start, session/briefing, session/live, assistant, voice |
| `test/core/`, `test/features/training/` | B | |
| `test/features/<others>/` | A | |

Create the project at M0 (B): `flutter create app --org com.rebase --platforms android`

## M0 stubs (so nobody waits)
- **B:** `ApiClient` with every method from `CONTRACT.md` §6.3, `MockApiClient` returning fixtures, `apiClientProvider`, `sessionStreamProvider`, all model classes (can start as thin `fromJson` wrappers), placeholder `TrainingHubScreen`.
- **A:** `AppTheme.dark()`, `buildRouter()` with every route pointing to placeholder screens (the `/training` route points to B's `TrainingHubScreen`), empty shared widgets with final constructors.

## Rules for Person A (UI)
- Screens get data **only** through `apiClientProvider` / `sessionStreamProvider` — never dio or sockets directly.
- All visible text through ARB files. Alert text looked up by alert `type`.
- Touch targets ≥ 56dp, dark high contrast, landscape. Alerts: colour + icon + text; sound + vibration for `critical`; one large tap to acknowledge.
- Voice: hold-to-talk (16 kHz mono wav) → `api.stt` → `api.ask` → `api.tts` → play. Always show the text too.
- Need a new API method or model field? Request it from B (progress file) — don't add it to `core/`.

## Rules for Person B (data layer + Training Hub)
- `ApiClient` method signatures are a contract (§6.3) — change only via the protocol.
- `USE_MOCK=true|false` via `--dart-define` switches the whole app between mock and real API.
- The mock must fake the WebSocket: telemetry every 1 s and a test alert every ~20 s, so A can build the live screen before the backend exists.
- Training Hub reuses A's theme and `ui/widgets/`; its text lives in `training_strings.dart`, not in A's ARB files.

## Both
- Run `flutter analyze` (and your tests) before every merge to `main`.
