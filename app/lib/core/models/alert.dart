/// CONTRACT §4 Alert / AlertCreate.
class AlertCreate {
  const AlertCreate({
    required this.type,
    required this.source,
    required this.severity,
    required this.message,
    required this.ts,
  });

  final String type; // AlertType
  final String source; // AlertSource: edge_cv | telemetry
  final String severity; // Severity
  final String message; // English, for the log
  final String ts; // ISO 8601 UTC

  Map<String, dynamic> toJson() => {
        'type': type,
        'source': source,
        'severity': severity,
        'message': message,
        'ts': ts,
      };
}

class Alert {
  const Alert({
    required this.id,
    required this.sessionId,
    required this.type,
    required this.source,
    required this.severity,
    required this.message,
    required this.ts,
    required this.acknowledged,
  });

  final String id;
  final String sessionId;
  final String type;
  final String source;
  final String severity;
  final String message;
  final String ts;
  final bool acknowledged;

  factory Alert.fromJson(Map<String, dynamic> j) => Alert(
        id: j['id'] as String,
        sessionId: j['session_id'] as String,
        type: j['type'] as String,
        source: j['source'] as String? ?? 'telemetry',
        severity: j['severity'] as String,
        message: j['message'] as String,
        ts: j['ts'] as String,
        acknowledged: j['acknowledged'] as bool? ?? false,
      );
}
