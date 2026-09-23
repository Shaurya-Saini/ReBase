import 'package:flutter_test/flutter_test.dart';

import 'package:app/core/api/mock_api_client.dart';
import 'package:app/core/models/models.dart';

void main() {
  final api = MockApiClient();

  test('login returns an operator with a language', () async {
    final op = await api.login('op_001', '1234');
    expect(op.id, 'op_001');
    expect(op.lang, isNotEmpty);
  });

  test('assignments embed a job + machine', () async {
    final a = await api.assignments('op_001');
    expect(a, isNotEmpty);
    expect(a.first.job.machineType, 'excavator');
    expect(a.first.machine.id, startsWith('mc_'));
  });

  test('estimate has a low/high range', () async {
    final e = await api.estimate('job_001');
    expect(e.rangeHours.length, 2);
    expect(e.rangeHours.first, lessThan(e.rangeHours.last));
  });

  test('checklist carries standard refs + a critical item', () async {
    final c = await api.checklist('ses_001');
    expect(c.standardRefs, isNotEmpty);
    expect(c.sections.first.items.any((i) => i.critical), isTrue);
  });

  test('postAlert → list → ack round-trips', () async {
    final created = await api.postAlert(
      'ses_001',
      AlertCreate(
        type: 'drowsiness',
        source: 'edge_cv',
        severity: 'critical',
        message: 'eyes closed',
        ts: DateTime.now().toUtc().toIso8601String(),
      ),
    );
    expect(created.acknowledged, isFalse);

    final list = await api.alerts('ses_001');
    expect(list.any((x) => x.id == created.id), isTrue);

    final acked = await api.ackAlert(created.id);
    expect(acked.acknowledged, isTrue);
  });
}
