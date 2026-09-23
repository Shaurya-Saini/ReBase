/// CONTRACT §4 Briefing (LLM, backend).
class Briefing {
  const Briefing({
    required this.sessionId,
    required this.lang,
    required this.machineSummary,
    required this.jobSummary,
    this.estimatedHours,
    required this.hazards,
    required this.reminders,
  });

  final String sessionId;
  final String lang;
  final String machineSummary;
  final String jobSummary;
  final double? estimatedHours;
  final List<String> hazards;
  final List<String> reminders;

  factory Briefing.fromJson(Map<String, dynamic> j) => Briefing(
        sessionId: j['session_id'] as String,
        lang: j['lang'] as String,
        machineSummary: j['machine_summary'] as String,
        jobSummary: j['job_summary'] as String,
        estimatedHours: (j['estimated_hours'] as num?)?.toDouble(),
        hazards: (j['hazards'] as List).map((e) => e as String).toList(),
        reminders: (j['reminders'] as List).map((e) => e as String).toList(),
      );
}
