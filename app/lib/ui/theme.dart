import 'package:flutter/material.dart';

/// A owns the app theme (CONTRACT §6.2). Dark, high-contrast, glove-friendly,
/// landscape tablet. B's Training Hub reuses this.
class AppTheme {
  /// Minimum glove-friendly touch target.
  static const double minTouch = 56.0;

  // Severity colours (AlertBanner + live screen). Never colour alone — always paired
  // with an icon + text (see AlertBanner).
  static const Color info = Color(0xFF3B82F6);
  static const Color warning = Color(0xFFF59E0B);
  static const Color critical = Color(0xFFEF4444);
  static const Color ok = Color(0xFF22C55E);

  static Color severityColor(String severity) => switch (severity) {
        'critical' => critical,
        'warning' => warning,
        _ => info,
      };

  static ThemeData dark() {
    const bg = Color(0xFF0E1116);
    const surface = Color(0xFF1A1F27);
    final base = ThemeData.dark(useMaterial3: true);
    return base.copyWith(
      scaffoldBackgroundColor: bg,
      colorScheme: base.colorScheme.copyWith(
        surface: surface,
        primary: const Color(0xFFFFC107),
        error: critical,
      ),
      textTheme: base.textTheme.apply(fontSizeFactor: 1.15),
      appBarTheme:
          const AppBarTheme(backgroundColor: surface, centerTitle: false),
      cardTheme: const CardThemeData(color: surface, margin: EdgeInsets.all(8)),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          minimumSize: const Size(minTouch * 2, minTouch),
          textStyle: const TextStyle(fontSize: 20, fontWeight: FontWeight.w600),
        ),
      ),
    );
  }
}
