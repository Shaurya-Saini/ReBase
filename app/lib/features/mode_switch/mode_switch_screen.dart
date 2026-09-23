import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// A0 placeholder. Mode switch (unmounted vs mounted) is refined in A2.
class ModeSwitchScreen extends StatelessWidget {
  const ModeSwitchScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Choose mode')),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            FilledButton(
              onPressed: () => context.go('/dashboard'),
              child: const Text('Unmounted (personal time)'),
            ),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: () => context.go('/session/ses_001/pre-start'),
              child: const Text('Mounted (start shift)'),
            ),
          ],
        ),
      ),
    );
  }
}
