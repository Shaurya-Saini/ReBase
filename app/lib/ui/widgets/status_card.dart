import 'package:flutter/material.dart';
import 'package:app/ui/theme.dart';

/// Rugged status tile: colored machine-style accent stripe, boxed icon, small
/// uppercase label, large bold value. CONTRACT §6.2.
class StatusCard extends StatelessWidget {
  const StatusCard({
    super.key,
    required this.title,
    required this.value,
    this.icon,
    this.color,
  });

  final String title;
  final String value;
  final IconData? icon;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final accent = color ?? AppTheme.amber;
    return Card(
      child: IntrinsicHeight(
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Container(width: 6, color: accent),
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(14),
                child: Row(
                  children: [
                    if (icon != null) ...[
                      Container(
                        padding: const EdgeInsets.all(8),
                        decoration: BoxDecoration(
                          color: accent.withValues(alpha: 0.15),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: Icon(icon, color: accent, size: 26),
                      ),
                      const SizedBox(width: 12),
                    ],
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Text(
                            title.toUpperCase(),
                            style: const TextStyle(
                                color: AppTheme.muted,
                                fontSize: 12,
                                fontWeight: FontWeight.w700,
                                letterSpacing: 0.8),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            value,
                            style: TextStyle(
                                color: color ?? AppTheme.offWhite,
                                fontSize: 24,
                                fontWeight: FontWeight.w800),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
