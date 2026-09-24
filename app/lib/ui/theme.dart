import 'package:flutter/material.dart';

/// Set to 'Inter' after bundling `assets/fonts/Inter-*.ttf` and declaring them
/// in pubspec. `null` = system font. The rugged identity comes from palette +
/// geometry regardless, so Inter drops in later with a one-line change.
const String? kFontFamily = null;

/// ReBase operator design system — "See it instantly. Act confidently."
/// Rugged, high-contrast, utilitarian: dark matte surfaces, amber highlights,
/// thick borders, machine-inspired geometry, large touch targets.
class AppTheme {
  static const double minTouch = 64.0; // glove-friendly

  // Palette
  static const Color charcoal = Color(0xFF171A1C);
  static const Color graphite = Color(0xFF252A2D);
  static const Color graphiteLight = Color(0xFF333A3E); // borders / raised
  static const Color amber = Color(0xFFF5A623); // safety / highlight / primary
  static const Color green = Color(0xFF39B86F); // signal / ok
  static const Color red = Color(0xFFE05252); // alert
  static const Color offWhite = Color(0xFFE8ECEB);
  static const Color muted = Color(0xFF9BA4A8);

  // Severity semantics
  static const Color info = amber;
  static const Color warning = amber;
  static const Color critical = red;
  static const Color ok = green;

  static Color severityColor(String severity) => switch (severity) {
        'critical' => red,
        'warning' => amber,
        'ok' => green,
        _ => amber,
      };

  static ThemeData dark() {
    final base = ThemeData.dark(useMaterial3: true);
    const scheme = ColorScheme.dark(
      primary: amber,
      onPrimary: charcoal,
      secondary: green,
      onSecondary: charcoal,
      surface: graphite,
      onSurface: offWhite,
      error: red,
      onError: charcoal,
    );

    OutlineInputBorder border(Color c, [double w = 2]) => OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: BorderSide(color: c, width: w),
        );

    return base.copyWith(
      scaffoldBackgroundColor: charcoal,
      colorScheme: scheme,
      textTheme: base.textTheme
          .apply(
              fontFamily: kFontFamily,
              bodyColor: offWhite,
              displayColor: offWhite)
          .copyWith(
            headlineSmall: base.textTheme.headlineSmall
                ?.copyWith(fontWeight: FontWeight.w800, color: offWhite),
            titleLarge: base.textTheme.titleLarge
                ?.copyWith(fontWeight: FontWeight.w700, color: offWhite),
            titleMedium: base.textTheme.titleMedium
                ?.copyWith(fontWeight: FontWeight.w700, color: offWhite),
            displaySmall: base.textTheme.displaySmall?.copyWith(
                fontWeight: FontWeight.w800,
                color: offWhite,
                letterSpacing: -1),
            labelLarge: base.textTheme.labelLarge
                ?.copyWith(fontWeight: FontWeight.w700, letterSpacing: 0.5),
          ),
      appBarTheme: const AppBarTheme(
        backgroundColor: charcoal,
        foregroundColor: offWhite,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: TextStyle(
            color: offWhite,
            fontSize: 22,
            fontWeight: FontWeight.w800,
            letterSpacing: 0.3),
      ),
      cardTheme: CardThemeData(
        color: graphite,
        elevation: 0,
        margin: const EdgeInsets.symmetric(vertical: 6, horizontal: 4),
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(10),
          side: const BorderSide(color: graphiteLight, width: 1.5),
        ),
      ),
      dividerTheme: const DividerThemeData(color: graphiteLight, thickness: 1),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: amber,
          foregroundColor: charcoal,
          minimumSize: const Size(minTouch, minTouch),
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          textStyle: const TextStyle(
              fontSize: 20, fontWeight: FontWeight.w800, letterSpacing: 0.5),
        ),
      ),
      outlinedButtonTheme: OutlinedButtonThemeData(
        style: OutlinedButton.styleFrom(
          foregroundColor: offWhite,
          minimumSize: const Size(0, 52),
          side: const BorderSide(color: graphiteLight, width: 2),
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
          textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700),
        ),
      ),
      segmentedButtonTheme: SegmentedButtonThemeData(
        style: ButtonStyle(
          side: const WidgetStatePropertyAll(
              BorderSide(color: graphiteLight, width: 2)),
          backgroundColor: WidgetStateProperty.resolveWith(
              (s) => s.contains(WidgetState.selected) ? amber : graphite),
          foregroundColor: WidgetStateProperty.resolveWith(
              (s) => s.contains(WidgetState.selected) ? charcoal : offWhite),
          textStyle: const WidgetStatePropertyAll(
              TextStyle(fontWeight: FontWeight.w700)),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: graphite,
        labelStyle: const TextStyle(color: muted, fontWeight: FontWeight.w600),
        border: border(graphiteLight),
        enabledBorder: border(graphiteLight),
        focusedBorder: border(amber, 2.5),
      ),
      listTileTheme: const ListTileThemeData(iconColor: amber),
      progressIndicatorTheme: const ProgressIndicatorThemeData(color: amber),
      snackBarTheme: const SnackBarThemeData(
        backgroundColor: graphiteLight,
        contentTextStyle:
            TextStyle(color: offWhite, fontWeight: FontWeight.w600),
      ),
    );
  }
}
