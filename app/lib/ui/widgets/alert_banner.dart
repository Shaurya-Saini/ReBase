import 'package:flutter/material.dart';
import 'package:app/ui/theme.dart';

/// Safety alert strip: full-bleed severity colour + icon + bold text (never
/// colour alone) + one big charcoal ACK. CONTRACT §6.2.
/// `severity` is 'info' | 'warning' | 'critical'.
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
    final bg = AppTheme.severityColor(severity);
    final fg = severity == 'critical' ? Colors.white : AppTheme.charcoal;
    return Material(
      color: bg,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(_icon, color: fg, size: 40),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(title,
                      style: TextStyle(
                          color: fg,
                          fontSize: 22,
                          fontWeight: FontWeight.w800,
                          letterSpacing: 0.3)),
                  Text(message,
                      style: TextStyle(
                          color: fg.withValues(alpha: 0.85),
                          fontSize: 16,
                          fontWeight: FontWeight.w600)),
                ],
              ),
            ),
            const SizedBox(width: 12),
            SizedBox(
              height: AppTheme.minTouch,
              child: FilledButton(
                style: FilledButton.styleFrom(
                    backgroundColor: AppTheme.charcoal,
                    foregroundColor: AppTheme.offWhite),
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
