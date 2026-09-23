import 'package:app/l10n/app_localizations.dart';

/// Localized alert label looked up by alert `type` (backend `message` stays
/// English for logs; the operator sees this).
String alertText(AppLocalizations t, String type) => switch (type) {
      'seatbelt_off' => t.alert_seatbelt_off,
      'drowsiness' => t.alert_drowsiness,
      'distraction' => t.alert_distraction,
      'operator_absent' => t.alert_operator_absent,
      'proximity' => t.alert_proximity,
      'excessive_idle' => t.alert_excessive_idle,
      'overheat' => t.alert_overheat,
      'overload' => t.alert_overload,
      'unsafe_operation' => t.alert_unsafe_operation,
      _ => type,
    };
