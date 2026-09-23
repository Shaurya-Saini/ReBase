import 'package:flutter_test/flutter_test.dart';
import 'package:app/edge/cv_decider.dart';

// Runs once B0 lands (needs pubspec). Verified now via a standalone dart run.
void main() {
  final t0 = DateTime(2026, 9, 23, 18, 0, 0);
  FaceObservation obs(int ms, {bool face = true, double? eye, double? yaw}) =>
      FaceObservation(
        ts: t0.add(Duration(milliseconds: ms)),
        facePresent: face,
        eyeOpenProb: eye,
        headYawDeg: yaw,
      );

  test('drowsiness fires only after eyes closed >= 2s, then re-arms', () {
    final d = CvDecider();
    expect(d.evaluate(obs(0, eye: 0.1)), isEmpty); // just closed
    expect(d.evaluate(obs(1000, eye: 0.1)), isEmpty); // 1s < 2s
    final fired = d.evaluate(obs(2100, eye: 0.1)); // 2.1s
    expect(fired.single.type, 'drowsiness');
    expect(fired.single.severity, 'critical');
    expect(fired.single.source, 'edge_cv');
    expect(d.evaluate(obs(2500, eye: 0.1)), isEmpty); // latched
    d.evaluate(obs(2600, eye: 0.9)); // eyes open -> clear
    expect(d.evaluate(obs(2700, eye: 0.1)), isEmpty); // window restarts
    expect(d.evaluate(obs(4800, eye: 0.1)).single.type, 'drowsiness');
  });

  test('distraction fires after sustained head turn', () {
    final d = CvDecider();
    expect(d.evaluate(obs(0, eye: 0.9, yaw: 50)), isEmpty);
    expect(d.evaluate(obs(2100, eye: 0.9, yaw: 50)).single.type, 'distraction');
  });

  test('absence fires after 3s of no face; eye/head ignored when absent', () {
    final d = CvDecider();
    expect(d.evaluate(obs(0, face: false)), isEmpty);
    expect(d.evaluate(obs(2000, face: false)), isEmpty);
    expect(d.evaluate(obs(3100, face: false)).single.type, 'operator_absent');
  });

  test('a brief blink does not trigger drowsiness', () {
    final d = CvDecider();
    d.evaluate(obs(0, eye: 0.1));
    d.evaluate(obs(300, eye: 0.9)); // opened after 300ms
    expect(d.evaluate(obs(2500, eye: 0.9)), isEmpty);
  });
}
