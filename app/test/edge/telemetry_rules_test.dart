import 'package:flutter_test/flutter_test.dart';
import 'package:app/edge/telemetry_rules.dart';

// Runs once B0 lands (needs pubspec). Verified now via tool/_verify_rules.dart.
void main() {
  group('TelemetryRuleEngine', () {
    late TelemetryRuleEngine e;
    setUp(() => e = TelemetryRuleEngine());

    Map<String, dynamic> normal() => {
          'engine_rpm': 1500,
          'hydraulic_temp_c': 60.0,
          'fuel_pct': 70,
          'load_pct': 40.0,
          'speed_kmh': 0.0,
          'idle_seconds': 0,
          'seatbelt': true,
          'proximity_m': 15.0,
        };

    test('normal telemetry raises nothing', () {
      expect(e.evaluate(normal()), isEmpty);
    });

    test('seatbelt off fires once, then debounces, then re-arms', () {
      final t = normal()..['seatbelt'] = false;
      final first = e.evaluate(t);
      expect(first.single.type, 'seatbelt_off');
      expect(first.single.severity, 'warning');
      expect(e.evaluate(t), isEmpty); // debounced while latched
      e.evaluate(normal()); // condition clears -> re-arm
      expect(e.evaluate(t).single.type, 'seatbelt_off');
    });

    test('seatbelt off escalates to critical while moving', () {
      e.evaluate(normal()..['seatbelt'] = false); // warning latched
      final moving = normal()
        ..['seatbelt'] = false
        ..['speed_kmh'] = 8.0;
      expect(e.evaluate(moving).single.severity, 'critical');
    });

    test('proximity is critical under 2 m', () {
      final a = e.evaluate(normal()..['proximity_m'] = 1.5).single;
      expect(a.type, 'proximity');
      expect(a.severity, 'critical');
    });

    test('overheat and overload can fire together', () {
      final t = normal()
        ..['hydraulic_temp_c'] = 110.0
        ..['load_pct'] = 105.0;
      final types = e.evaluate(t).map((a) => a.type).toSet();
      expect(types, containsAll(['overheat', 'overload']));
    });

    test('unsafe operation: fast under heavy load', () {
      final t = normal()
        ..['speed_kmh'] = 20.0
        ..['load_pct'] = 85.0;
      final types = e.evaluate(t).map((a) => a.type).toSet();
      expect(types, contains('unsafe_operation'));
    });
  });
}
