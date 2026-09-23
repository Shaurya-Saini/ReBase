import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

/// A0 placeholder. Real login (operator picker + PIN + language) is A2.
class LoginScreen extends StatelessWidget {
  const LoginScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('ReBase — Login')),
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Text('TODO A2: operator picker + PIN + language'),
            const SizedBox(height: 16),
            FilledButton(
              onPressed: () => context.go('/mode'),
              child: const Text('Continue'),
            ),
          ],
        ),
      ),
    );
  }
}
