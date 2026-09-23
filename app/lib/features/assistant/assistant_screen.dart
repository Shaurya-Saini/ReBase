import 'package:flutter/material.dart';

/// A0 placeholder. Real assistant chat + voice loop (E23/E24, on-device STT) is A10/A11.
class AssistantScreen extends StatelessWidget {
  const AssistantScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Manual assistant')),
      body: const Center(
        child: Text('TODO A11: RAG Q&A chat + hold-to-talk voice loop'),
      ),
    );
  }
}
