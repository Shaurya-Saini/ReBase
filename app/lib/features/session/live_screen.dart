import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// A0 placeholder. Real live session (gauges from WS, on-device alerts, ack,
/// summary) is A7; the edge rule engine (A8) and camera CV (A9) feed it.
class LiveScreen extends StatelessWidget {
  const LiveScreen({super.key, required this.sessionId});

  final String sessionId;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Live session')),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('TODO A7: telemetry gauges + alerts for $sessionId'),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: () => context.go('/assistant'),
              child: const Text('Ask the assistant'),
            ),
            const SizedBox(height: 8),
            FilledButton(
              onPressed: () => context.go('/dashboard'),
              child: const Text('End session'),
            ),
          ],
        ),
      ),
    );
  }
}
