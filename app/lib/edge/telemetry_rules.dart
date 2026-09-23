// A owns lib/edge/ — on-device safety. See CONTRACT §5 (telemetry) + §2 (alert table).
// Skeleton for A8: threshold rule engine over the WebSocket telemetry stream.

/// Draft of the alert the app POSTs to E18.
/// TODO A8: replace with the core `AlertCreate` model once B exposes it (§6.1).
class AlertDraft {
  AlertDraft({
    required this.type,
    required this.source,
    required this.severity,
    required this.message,
  });

  final String type; // AlertType (CONTRACT §2)
  final String source; // 'telemetry' here; 'edge_cv' for the camera monitor
  final String severity; // Severity
  final String message; // English, for the incident log
}

/// All tunable thresholds in one place so they're easy to adjust for the demo.
class TelemetryThresholds {
  static const double hydraulicTempC = 95.0; // overheat
  static const double proximityM = 5.0; // proximity hazard (person too close)
  static const int idleSeconds = 180; // excessive idle
  static const int loadPct = 95; // overload
}

/// TODO A8: consume Telemetry ticks (CONTRACT §5), apply the rules below and emit
/// AlertDrafts, debounced per type so each occurrence fires once.
class TelemetryRuleEngine {
  final Map<String, DateTime> _lastFired = {};

  /// [data] is the `telemetry.data` map from CONTRACT §5.
  List<AlertDraft> evaluate(Map<String, dynamic> data) {
    // TODO A8: seatbelt_off, proximity, excessive_idle, overheat, overload, unsafe_operation.
    _lastFired.clear(); // placeholder to avoid unused-field lint; remove in A8.
    return const [];
  }
}
