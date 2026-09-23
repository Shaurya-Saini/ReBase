import 'package:flutter/material.dart';
import 'package:app/ui/theme.dart';

/// Safety alert banner: colour + icon + text (never colour alone) + one big ack tap.
/// CONTRACT §6.2. `severity` is 'info' | 'warning' | 'critical'.
class AlertBanner extends StatelessWidget {
  const AlertBanner({
    super.key,
    required this.title,
    required this.message,
    required this.severity,
    required this.onAck,
  });

  final String title;
  final String message;
  final String severity;
  final VoidCallback onAck;

  IconData get _icon => switch (severity) {
        'critical' => Icons.error,
        'warning' => Icons.warning_amber,
        _ => Icons.info,
      };

  @override
  Widget build(BuildContext context) {
    return Material(
      color: AppTheme.severityColor(severity),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(_icon, color: Colors.black, size: 40),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(title,
                      style: const TextStyle(
                          color: Colors.black,
                          fontSize: 22,
                          fontWeight: FontWeight.bold)),
                  Text(message,
                      style:
                          const TextStyle(color: Colors.black87, fontSize: 18)),
                ],
              ),
            ),
            const SizedBox(width: 12),
            SizedBox(
              height: AppTheme.minTouch,
              child: FilledButton(
                style: FilledButton.styleFrom(
                    backgroundColor: Colors.black,
                    foregroundColor: Colors.white),
                onPressed: onAck,
                child: const Text('ACK'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
