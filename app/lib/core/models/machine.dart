/// CONTRACT §4 Machine.
class Machine {
  const Machine({
    required this.id,
    required this.type,
    required this.model,
    required this.serial,
    required this.hourMeter,
    required this.status,
    this.lastInspection,
  });

  final String id;
  final String type; // MachineType
  final String model;
  final String serial;
  final double hourMeter;
  final String status; // MachineStatus
  final String? lastInspection;

  factory Machine.fromJson(Map<String, dynamic> j) => Machine(
        id: j['id'] as String,
        type: j['type'] as String,
        model: j['model'] as String,
        serial: j['serial'] as String,
        hourMeter: (j['hour_meter'] as num).toDouble(),
        status: j['status'] as String,
        lastInspection: j['last_inspection'] as String?,
      );
}
