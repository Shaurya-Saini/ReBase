// A9 — real on-device computer vision via Google ML Kit face detection.
// This file is the plugin glue (camera + FaceDetector); the decision logic lives
// in cv_decider.dart so it can be unit-tested without a device.

import 'dart:async';

import 'package:app/edge/cv_decider.dart';
import 'package:app/edge/telemetry_rules.dart' show AlertDraft;

/// Runs the front camera through ML Kit, converts each detected face into a
/// [FaceObservation], and emits [AlertDraft]s via [CvDecider].
class CvMonitor {
  final CvDecider _decider = CvDecider();
  final StreamController<AlertDraft> _out =
      StreamController<AlertDraft>.broadcast();

  Stream<AlertDraft> get alerts => _out.stream;

  Future<void> start() async {
    // TODO A9: start `camera` (front, low res) + ML Kit `FaceDetector`
    // (enableClassification for eye-open prob, enableTracking). For each frame,
    // build a FaceObservation and call [onObservation].
  }

  /// Feed a derived observation (called from the ML Kit frame callback, or by
  /// tests). Pushes any resulting alerts to [alerts].
  void onObservation(FaceObservation o) {
    for (final a in _decider.evaluate(o)) {
      _out.add(a);
    }
  }

  Future<void> stop() async {
    // TODO A9: dispose camera + detector.
    await _out.close();
  }
}
