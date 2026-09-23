/// Build-time configuration via --dart-define.
/// `USE_MOCK=true` (default) runs the whole app on in-memory fixtures with no
/// backend; `false` hits the real API at `API_BASE`.
class AppConfig {
  static const bool useMock =
      bool.fromEnvironment('USE_MOCK', defaultValue: true);

  static const String apiBase = String.fromEnvironment(
    'API_BASE',
    defaultValue: 'http://10.0.2.2:8000', // Android emulator → host machine
  );
}
