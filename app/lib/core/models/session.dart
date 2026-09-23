/// CONTRACT §4 Session / SessionSummary.
class Session {
  const Session({
    required this.id,
    required this.operatorId,
    required this.machineId,
    required this.jobId,
    required this.state,
    this.startedAt,
    this.endedAt,
  });

  final String id;
  final String operatorId;
  final String machineId;
  final String jobId;
  final String state; // SessionState
  final String? startedAt;
  final String? endedAt;

  factory Session.fromJson(Map<String, dynamic> j) => Session(
        id: j['id'] as String,
        operatorId: j['operator_id'] as String,
        machineId: j['machine_id'] as String,
        jobId: j['job_id'] as String,
        state: j['state'] as String,
        startedAt: j['started_at'] as String?,
        endedAt: j['ended_at'] as String?,
      );
}

class SessionSummary {
  const SessionSummary({
    required this.sessionId,
    required this.durationHours,
    required this.alertsTotal,
    required this.alertsCritical,
    required this.idleMinutes,
  });

  final String sessionId;
  final double durationHours;
  final int alertsTotal;
  final int alertsCritical;
  final int idleMinutes;

  factory SessionSummary.fromJson(Map<String, dynamic> j) => SessionSummary(
        sessionId: j['session_id'] as String,
        durationHours: (j['duration_hours'] as num).toDouble(),
        alertsTotal: (j['alerts_total'] as num).toInt(),
        alertsCritical: (j['alerts_critical'] as num).toInt(),
        idleMinutes: (j['idle_minutes'] as num).toInt(),
      );
}
