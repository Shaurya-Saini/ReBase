// A owns lib/edge/ — on-device safety. See CONTRACT §5 (telemetry) + §2 (alert table).
// Threshold rule engine over the WebSocket telemetry stream (A8).
// Pure Dart (no Flutter/package imports) so it is unit-testable in isolation.

/// Draft of the alert the app POSTs to the backend incident log (E18).
/// Kept local so the engine has no dependency on the data layer; converted to
/// the core `AlertCreate` model by the dispatcher at integration.
class AlertDraft {
  AlertDraft({
    required this.type,
    required this.severity,
    required this.message,
    this.source = 'telemetry',
  });

  final String type; // AlertType (CONTRACT §2)
  final String source; // 'telemetry' here; 'edge_cv' for the camera monitor
  final String severity; // 'info' | 'warning' | 'critical'
  final String message; // English, for the incident log

  @override
  String toString() => '[$severity] $type: $message';
}

/// All tunable thresholds in one place so they're easy to adjust for the demo.
class TelemetryThresholds {
  static const double overheatWarnC = 95;
  static const double overheatCritC = 105;
  static const double proximityWarnM = 5;
  static const double proximityCritM = 2;
  static const int idleWarnSeconds = 180;
  static const double overloadWarnPct = 90;
  static const double overloadCritPct = 100;
  static const double unsafeSpeedKmh = 15;
  static const double unsafeLoadPct = 80;
  static const double movingSpeedKmh = 0.5;
}

/// Edge-triggered rule engine: each alert type fires once when its condition
/// becomes true (and again if it escalates in severity), and re-arms when the
/// condition clears — so a sustained hazard doesn't spam the operator.
class TelemetryRuleEngine {
  final Map<String, int> _active = {}; // type -> latched severity rank

  static int _rank(String s) => switch (s) {
        'critical' => 3,
        'warning' => 2,
        _ => 1,
      };

  /// [data] is the `telemetry.data` map (CONTRACT §5). Returns alerts to POST.
  List<AlertDraft> evaluate(Map<String, dynamic> data) {
    final out = <AlertDraft>[];

    double? d(String k) => (data[k] as num?)?.toDouble();
    int? asInt(String k) => (data[k] as num?)?.toInt();

    void consider(String type, bool active, String severity, String message) {
      if (active) {
        final r = _rank(severity);
        if (r > (_active[type] ?? 0)) {
          out.add(AlertDraft(type: type, severity: severity, message: message));
          _active[type] = r;
        }
      } else {
        _active.remove(type);
      }
    }

    final speed = d('speed_kmh') ?? 0;

    // Seatbelt — escalates to critical while the machine is moving.
    final seatbelt = data['seatbelt'] as bool?;
    if (seatbelt == false) {
      final moving = speed > TelemetryThresholds.movingSpeedKmh;
      consider(
        'seatbelt_off',
        true,
        moving ? 'critical' : 'warning',
        moving
            ? 'Seatbelt not fastened while machine is moving'
            : 'Seatbelt not fastened',
      );
    } else {
      consider('seatbelt_off', false, 'warning', '');
    }

    // Proximity hazard — person/obstacle too close.
    final prox = d('proximity_m');
    if (prox != null) {
      final msg = 'Person or obstacle within ${prox.toStringAsFixed(1)} m';
      if (prox < TelemetryThresholds.proximityCritM) {
        consider('proximity', true, 'critical', msg);
      } else if (prox < TelemetryThresholds.proximityWarnM) {
        consider('proximity', true, 'warning', msg);
      } else {
        consider('proximity', false, 'warning', '');
      }
    }

    // Excessive idle.
    final idle = asInt('idle_seconds');
    consider(
      'excessive_idle',
      idle != null && idle > TelemetryThresholds.idleWarnSeconds,
      'warning',
      'Excessive idling (${idle ?? 0} s)',
    );

    // Overheat.
    final temp = d('hydraulic_temp_c');
    if (temp != null) {
      final msg = 'Hydraulic temperature ${temp.toStringAsFixed(0)} °C';
      if (temp > TelemetryThresholds.overheatCritC) {
        consider('overheat', true, 'critical', msg);
      } else if (temp > TelemetryThresholds.overheatWarnC) {
        consider('overheat', true, 'warning', msg);
      } else {
        consider('overheat', false, 'warning', '');
      }
    }

    // Overload.
    final load = d('load_pct');
    if (load != null) {
      final msg = 'Load at ${load.toStringAsFixed(0)}% of rated';
      if (load > TelemetryThresholds.overloadCritPct) {
        consider('overload', true, 'critical', msg);
      } else if (load > TelemetryThresholds.overloadWarnPct) {
        consider('overload', true, 'warning', msg);
      } else {
        consider('overload', false, 'warning', '');
      }
    }

    // Unsafe operation — moving fast under heavy load.
    final unsafe = load != null &&
        speed > TelemetryThresholds.unsafeSpeedKmh &&
        load > TelemetryThresholds.unsafeLoadPct;
    consider(
      'unsafe_operation',
      unsafe,
      'warning',
      'Traveling at ${speed.toStringAsFixed(0)} km/h under heavy load',
    );

    return out;
  }
}
