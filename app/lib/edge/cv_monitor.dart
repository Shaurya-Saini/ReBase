// Skeleton for A9 — real on-device computer vision via Google ML Kit face detection.
// Emits edge_cv alerts (drowsiness / distraction / operator_absent) from the front camera.

import 'package:app/edge/telemetry_rules.dart' show AlertDraft;

/// TODO A9: wire `google_mlkit_face_detection` to the front `camera` stream.
/// Heuristics (tune on-device):
///   - eye-open probability < ~0.3 sustained > 2 s  -> drowsiness (critical)
///   - head Euler Y beyond ±35° sustained            -> distraction (warning)
///   - no face detected > 3 s                        -> operator_absent (warning)
class CvMonitor {
  Future<void> start() async {
    // TODO A9: start camera + FaceDetector, push results through [alerts].
  }

  Future<void> stop() async {
    // TODO A9: dispose camera + detector.
  }

  /// Stream of camera-derived alerts.
  Stream<AlertDraft> get alerts => const Stream.empty();
}
