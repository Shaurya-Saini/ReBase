/// CONTRACT §5 telemetry stream payload (machine sensors only; operator state
/// is decided on-device by the camera CV).
class Telemetry {
  const Telemetry({
    required this.ts,
    required this.engineRpm,
    required this.hydraulicTempC,
    required this.fuelPct,
    required this.loadPct,
    required this.speedKmh,
    required this.idleSeconds,
    required this.seatbelt,
    required this.proximityM,
  });

  final String ts;
  final int engineRpm;
  final double hydraulicTempC;
  final int fuelPct;
  final double loadPct;
  final double speedKmh;
  final int idleSeconds;
  final bool seatbelt;
  final double proximityM;

  /// The `data` map shape the edge rule engine consumes (CONTRACT §5).
  Map<String, dynamic> toData() => {
        'engine_rpm': engineRpm,
        'hydraulic_temp_c': hydraulicTempC,
        'fuel_pct': fuelPct,
        'load_pct': loadPct,
        'speed_kmh': speedKmh,
        'idle_seconds': idleSeconds,
        'seatbelt': seatbelt,
        'proximity_m': proximityM,
      };

  /// Parse a full `{type:telemetry, ts, data:{...}}` websocket message.
  factory Telemetry.fromWsMessage(Map<String, dynamic> msg) {
    final d = msg['data'] as Map<String, dynamic>;
    return Telemetry(
      ts: msg['ts'] as String? ?? DateTime.now().toUtc().toIso8601String(),
      engineRpm: (d['engine_rpm'] as num).toInt(),
      hydraulicTempC: (d['hydraulic_temp_c'] as num).toDouble(),
      fuelPct: (d['fuel_pct'] as num).toInt(),
      loadPct: (d['load_pct'] as num).toDouble(),
      speedKmh: (d['speed_kmh'] as num).toDouble(),
      idleSeconds: (d['idle_seconds'] as num).toInt(),
      seatbelt: d['seatbelt'] as bool,
      proximityM: (d['proximity_m'] as num).toDouble(),
    );
  }
}
