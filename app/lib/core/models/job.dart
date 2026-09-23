/// CONTRACT §4 Job.
class Job {
  const Job({
    required this.id,
    required this.projectId,
    required this.title,
    required this.site,
    required this.machineType,
    required this.scheduledStart,
    required this.plannedHours,
    required this.status,
  });

  final String id;
  final String projectId;
  final String title;
  final String site;
  final String machineType;
  final String scheduledStart;
  final double plannedHours;
  final String status; // JobStatus

  factory Job.fromJson(Map<String, dynamic> j) => Job(
        id: j['id'] as String,
        projectId: j['project_id'] as String,
        title: j['title'] as String,
        site: j['site'] as String,
        machineType: j['machine_type'] as String,
        scheduledStart: j['scheduled_start'] as String,
        plannedHours: (j['planned_hours'] as num).toDouble(),
        status: j['status'] as String,
      );
}
