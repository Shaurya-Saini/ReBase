import 'dart:convert';
import 'dart:math';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:web_socket_channel/web_socket_channel.dart';

import 'package:app/core/config.dart';
import 'package:app/core/models/telemetry.dart';

/// Telemetry stream for a session (CONTRACT §5).
/// - `USE_MOCK=true`: a fake 1 Hz generator so the live gauges + edge rule
///   engine work with no backend.
/// - `USE_MOCK=false`: the real backend WebSocket `/ws/sessions/{id}`. The
///   simulator (steered via `POST /sim/scenario`) changes these values so the
///   on-device rules fire — that's the demo control.
final telemetryStreamProvider =
    StreamProvider.family<Telemetry, String>((ref, sessionId) {
  return AppConfig.useMock
      ? mockTelemetryStream()
      : backendTelemetryStream(sessionId);
});

Stream<Telemetry> backendTelemetryStream(String sessionId) async* {
  final wsBase = AppConfig.apiBase.replaceFirst('http', 'ws');
  final channel =
      WebSocketChannel.connect(Uri.parse('$wsBase/ws/sessions/$sessionId'));
  try {
    await for (final raw in channel.stream) {
      final msg = jsonDecode(raw as String) as Map<String, dynamic>;
      if (msg['type'] == 'telemetry') {
        yield Telemetry.fromWsMessage(msg);
      }
    }
  } finally {
    await channel.sink.close();
  }
}

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
