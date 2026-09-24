import 'package:tflite_flutter/tflite_flutter.dart';

import 'package:app/core/models/telemetry.dart';
import 'package:app/edge/telemetry_rules.dart' show AlertDraft;

/// Learned telemetry safety model. Loads a quantized TFLite model (trained by
/// `ml/`) and classifies each telemetry tick into an alert class. If the asset
/// isn't bundled it stays `isLoaded == false` and the live screen keeps using
/// the rule engine — so the app always works.
class EdgeSafetyModel {
  Interpreter? _interp;

  // Keep in sync with ml/train.py (LABELS / SCALE).
  static const List<String> _labels = [
    'normal',
    'seatbelt_off',
    'proximity',
    'excessive_idle',
    'overheat',
    'overload',
    'unsafe_operation',
  ];
  static const List<double> _scale = [
    3000, 150, 100, 150, 40, 600, 1, 30, //
  ];
  static const Map<String, String> _severity = {
    'seatbelt_off': 'critical',
    'proximity': 'critical',
    'overload': 'critical',
    'excessive_idle': 'warning',
    'overheat': 'warning',
    'unsafe_operation': 'warning',
  };

  final Map<String, bool> _latched = {};

  bool get isLoaded => _interp != null;

  Future<void> load() async {
    try {
      _interp = await Interpreter.fromAsset('assets/models/safety.tflite');
    } catch (_) {
      _interp = null; // no model bundled -> caller falls back to rules
    }
  }

  List<double> _features(Telemetry t) => [
        t.engineRpm / _scale[0],
        t.hydraulicTempC / _scale[1],
        t.fuelPct / _scale[2],
        t.loadPct / _scale[3],
        t.speedKmh / _scale[4],
        t.idleSeconds / _scale[5],
        t.seatbelt ? 1.0 : 0.0,
        t.proximityM / _scale[7],
      ];

  /// Edge-triggered: fires once when the predicted class becomes active and
  /// re-arms when the prediction returns to `normal`.
  List<AlertDraft> evaluate(Telemetry t) {
    final interp = _interp;
    if (interp == null) return const [];

    final output = [List<double>.filled(_labels.length, 0.0)];
    try {
      interp.run([_features(t)], output);
    } catch (_) {
      _interp = null; // incompatible model -> disable, fall back to rules
      return const [];
    }

    final probs = output[0];
    var arg = 0;
    for (var i = 1; i < probs.length; i++) {
      if (probs[i] > probs[arg]) arg = i;
    }
    final label = _labels[arg];

    _latched.removeWhere((k, _) => k != label); // re-arm everything else
    if (label == 'normal' || (_latched[label] ?? false)) return const [];

    _latched[label] = true;
    return [
      AlertDraft(
        type: label,
        source: 'telemetry',
        severity: _severity[label] ?? 'warning',
        message: 'Edge model detected $label',
      ),
    ];
  }

  void close() => _interp?.close();
}
