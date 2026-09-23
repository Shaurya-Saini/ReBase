import 'dart:math';

import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:app/core/models/telemetry.dart';

/// Telemetry stream for a session (CONTRACT §5). M1: a fake 1 Hz generator so
/// the live gauges + edge rule engine work without a backend. A17 swaps in a
/// real WebSocket (`web_socket_channel`) when `USE_MOCK=false`.
final telemetryStreamProvider =
    StreamProvider.family<Telemetry, String>((ref, sessionId) {
  return mockTelemetryStream();
});

Stream<Telemetry> mockTelemetryStream() async* {
  final rnd = Random();
  var idle = 0;
  while (true) {
    await Future<void>.delayed(const Duration(seconds: 1));
    final moving = rnd.nextDouble() < 0.5;
    idle = moving ? 0 : idle + 1;
    yield Telemetry(
      ts: DateTime.now().toUtc().toIso8601String(),
      engineRpm: 800 + rnd.nextInt(1600),
      hydraulicTempC: 55 + rnd.nextDouble() * 20,
      fuelPct: 40 + rnd.nextInt(50),
      loadPct: moving ? 30 + rnd.nextDouble() * 40 : rnd.nextDouble() * 10,
      speedKmh: moving ? rnd.nextDouble() * 8 : 0,
      idleSeconds: idle,
      seatbelt: true,
      proximityM: 8 + rnd.nextDouble() * 10,
    );
  }
}
