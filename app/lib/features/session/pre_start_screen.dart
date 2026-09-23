import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// A0 placeholder. Real pre-start checklist + defect gating (E12–E14) is A5.
class PreStartScreen extends StatelessWidget {
  const PreStartScreen({super.key, required this.sessionId});

  final String sessionId;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Pre-start checklist')),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('TODO A5: checklist for $sessionId (critical-defect gate)'),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: () => context.go('/session/$sessionId/briefing'),
              child: const Text('Complete → briefing'),
            ),
          ],
        ),
      ),
    );
  }
}
