import 'package:app/core/models/job.dart';
import 'package:app/core/models/machine.dart';

/// CONTRACT §4 Assignment (embeds Job + Machine).
class Assignment {
  const Assignment({
    required this.id,
    required this.operatorId,
    required this.date,
    required this.shift,
    required this.job,
    required this.machine,
  });

  final String id;
  final String operatorId;
  final String date;
  final String shift; // Shift
  final Job job;
  final Machine machine;

  factory Assignment.fromJson(Map<String, dynamic> j) => Assignment(
        id: j['id'] as String,
        operatorId: j['operator_id'] as String,
        date: j['date'] as String,
        shift: j['shift'] as String,
        job: Job.fromJson(j['job'] as Map<String, dynamic>),
        machine: Machine.fromJson(j['machine'] as Map<String, dynamic>),
      );
}
