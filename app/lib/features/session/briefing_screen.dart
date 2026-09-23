import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// A0 placeholder. Real briefing screen + read-aloud (E15, TTS) is A6.
class BriefingScreen extends StatelessWidget {
  const BriefingScreen({super.key, required this.sessionId});

  final String sessionId;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Operational briefing')),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('TODO A6: briefing for $sessionId + read-aloud'),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: () => context.go('/session/$sessionId/live'),
              child: const Text('Start work'),
            ),
          ],
        ),
      ),
    );
  }
}
