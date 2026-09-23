import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// A0 placeholder. Real unmounted dashboard (today/week/month + hours & rest) is A3.
class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.school),
            tooltip: 'Training Hub',
            onPressed: () =>
                context.go('/training?operatorId=op_001&machineType=excavator'),
          ),
        ],
      ),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('TODO A3: assignments (day/week/month) + hours & rest'),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: () => context.go('/job/job_001'),
              child: const Text('Open today\'s job'),
            ),
          ],
        ),
      ),
    );
  }
}
