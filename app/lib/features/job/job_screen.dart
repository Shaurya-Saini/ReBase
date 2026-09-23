import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// A0 placeholder. Real job detail + estimate (E7, E8) is A4.
class JobScreen extends StatelessWidget {
  const JobScreen({super.key, required this.jobId});

  final String jobId;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Job $jobId')),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text('TODO A4: job detail + XGBoost estimate for $jobId'),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: () => context.go('/session/ses_001/pre-start'),
              child: const Text('Start session'),
            ),
          ],
        ),
      ),
    );
  }
}
