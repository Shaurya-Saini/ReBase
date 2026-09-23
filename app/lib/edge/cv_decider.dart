// A owns lib/edge/ — on-device safety. Decision logic for the camera CV (A9).
// Pure Dart (no Flutter/ML Kit imports) so the "brain" is unit-testable in
// isolation; cv_monitor.dart feeds it real ML Kit observations.

import 'package:app/edge/telemetry_rules.dart' show AlertDraft;

/// One frame's worth of face signals derived from ML Kit face detection.
class FaceObservation {
  FaceObservation({
    required this.ts,
    required this.facePresent,
    this.eyeOpenProb, // min of left/right eye-open probability, 0..1
    this.headYawDeg, // Euler Y; + = looking right, - = looking left
  });

  final DateTime ts;
  final bool facePresent;
  final double? eyeOpenProb;
  final double? headYawDeg;
}

class CvThresholds {
  static const double eyeOpenClosed = 0.30; // below this = eyes closed
  static const double headYawDeg = 35; // beyond this = looking away
  static const int drowsyMs = 2000; // sustained closed -> drowsiness
  static const int distractMs = 2000; // sustained turned -> distraction
  static const int absentMs = 3000; // sustained no-face -> absence
}

/// Emits an edge_cv alert once a condition is sustained past its threshold, and
/// re-arms when it clears — so a genuine, held state fires rather than a blink.
class CvDecider {
  final Map<String, DateTime> _since = {}; // condition -> first-seen ts
  final Set<String> _latched = {};

  List<AlertDraft> evaluate(FaceObservation o) {
    final out = <AlertDraft>[];

    void track(
      String key,
      bool condition,
      int sustainMs,
      String type,
      String severity,
      String message,
    ) {
      if (condition) {
        final start = _since[key] ??= o.ts;
        if (!_latched.contains(key) &&
            o.ts.difference(start).inMilliseconds >= sustainMs) {
          out.add(AlertDraft(
              type: type,
              source: 'edge_cv',
              severity: severity,
              message: message));
          _latched.add(key);
        }
      } else {
        _since.remove(key);
        _latched.remove(key);
      }
    }

    // No face at all — eye/head signals are meaningless, so only absence applies.
    track('absent', !o.facePresent, CvThresholds.absentMs, 'operator_absent',
        'warning', 'Operator not detected in cab');

    final eyesClosed = o.facePresent &&
        o.eyeOpenProb != null &&
        o.eyeOpenProb! < CvThresholds.eyeOpenClosed;
    track('drowsy', eyesClosed, CvThresholds.drowsyMs, 'drowsiness', 'critical',
        'Operator eyes closed for more than 2 seconds');

    final turned = o.facePresent &&
        o.headYawDeg != null &&
        o.headYawDeg!.abs() > CvThresholds.headYawDeg;
    track('distract', turned, CvThresholds.distractMs, 'distraction', 'warning',
        'Operator looking away from the task');

    return out;
  }
}
