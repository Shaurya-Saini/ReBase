import 'package:flutter/material.dart';
import 'package:app/ui/theme.dart';

/// Large, glove-friendly primary action button. Reused across A's screens and
/// B's Training Hub (CONTRACT §6.2).
class BigButton extends StatelessWidget {
  const BigButton({
    super.key,
    required this.label,
    required this.onPressed,
    this.icon,
  });

  final String label;
  final VoidCallback? onPressed;
  final IconData? icon;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      height: AppTheme.minTouch + 8,
      width: double.infinity,
      child: FilledButton.icon(
        onPressed: onPressed,
        icon: Icon(icon ?? Icons.chevron_right, size: 28),
        label: Text(label),
      ),
    );
  }
}
