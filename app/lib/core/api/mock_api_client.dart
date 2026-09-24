import 'dart:typed_data';

import 'package:app/core/api/api_client.dart';
import 'package:app/core/api/mock_data.dart';
import 'package:app/core/models/models.dart';

/// Fixture-backed client for `USE_MOCK=true`. Stateful for alerts so the live
/// screen's post → list → ack loop works offline.
class MockApiClient implements ApiClient {
  final List<Alert> _alerts = [];
  int _seq = 0;

  Future<T> _delay<T>(T v) =>
      Future.delayed(const Duration(milliseconds: 120), () => v);

  @override
  Future<Operator> login(String operatorId, String pin) =>
      _delay(MockData.operators()
          .firstWhere((o) => o.id == operatorId, orElse: MockData.operator1));

  @override
  Future<List<Operator>> operators() => _delay(MockData.operators());

  @override
  Future<Operator> operatorById(String id) => _delay(MockData.operators()
      .firstWhere((o) => o.id == id, orElse: MockData.operator1));

  @override
  Future<List<Assignment>> assignments(String operatorId,
          {String range = 'day'}) =>
      _delay([MockData.assignment1()]);

  @override
  Future<List<Machine>> machines() => _delay(MockData.machines());

  @override
  Future<Machine> machine(String id) => _delay(MockData.machines()
      .firstWhere((m) => m.id == id, orElse: MockData.machine1));

  @override
  Future<Job> job(String id) => _delay(MockData.job1());

  @override
  Future<Estimate> estimate(String jobId) => _delay(MockData.estimate1());

  @override
  Future<Session> createSession({
    required String operatorId,
    required String machineId,
    required String jobId,
  }) =>
      _delay(MockData.session1());

  @override
  Future<Session> session(String id) => _delay(MockData.session1());

  @override
  Future<Checklist> checklist(String sessionId) =>
      _delay(MockData.checklist1(sessionId));

  @override
  Future<ChecklistItem> updateChecklistItem(
    String sessionId,
    String itemId, {
    required String status,
    String? note,
  }) =>
      _delay(ChecklistItem(
          id: itemId, text: '', critical: false, status: status, note: note));

  @override
  Future<Session> completeChecklist(String sessionId) =>
      _delay(MockData.session1(state: 'briefing'));

  @override
  Future<Briefing> briefing(String sessionId, {String lang = 'en-IN'}) =>
      _delay(MockData.briefing1(sessionId, lang));

  @override
  Future<Session> startSession(String sessionId) =>
      _delay(MockData.session1(state: 'active'));

  @override
  Future<SessionSummary> endSession(String sessionId) =>
      _delay(MockData.summary1(sessionId));

  @override
  Future<Alert> postAlert(String sessionId, AlertCreate a) {
    final alert = Alert(
      id: 'alr_${(++_seq).toString().padLeft(3, '0')}',
      sessionId: sessionId,
      type: a.type,
      source: a.source,
      severity: a.severity,
      message: a.message,
      ts: a.ts,
      acknowledged: false,
    );
    _alerts.add(alert);
    return _delay(alert);
  }

  @override
  Future<List<Alert>> alerts(String sessionId) =>
      _delay(_alerts.where((x) => x.sessionId == sessionId).toList());

  @override
  Future<Alert> ackAlert(String alertId) {
    final i = _alerts.indexWhere((x) => x.id == alertId);
    if (i >= 0) {
      final o = _alerts[i];
      _alerts[i] = Alert(
        id: o.id,
        sessionId: o.sessionId,
        type: o.type,
        source: o.source,
        severity: o.severity,
        message: o.message,
        ts: o.ts,
        acknowledged: true,
      );
      return _delay(_alerts[i]);
    }
    return _delay(Alert(
      id: alertId,
      sessionId: '',
      type: 'unknown',
      source: 'telemetry',
      severity: 'info',
      message: '',
      ts: DateTime.now().toUtc().toIso8601String(),
      acknowledged: true,
    ));
  }

  @override
  Future<AssistantAnswer> ask(AssistantRequest req) =>
      _delay(MockData.answer1(req.lang));

  @override
  Future<Uint8List> tts(String text, String lang) => _delay(Uint8List(0));

  @override
  Future<String> translate(String text, String target) => _delay(text);

  @override
  Future<TrainingModule> nextTraining(String operatorId, String machineType) =>
      _delay(MockData.training1(machineType, 'novice'));

  @override
  Future<void> completeTraining(
    String moduleId, {
    required String operatorId,
    required int score,
  }) =>
      _delay<void>(null);

  @override
  Future<List<String>> simScenarios() => _delay(const [
        'normal',
        'seatbelt_off',
        'proximity',
        'excessive_idle',
        'overheat',
        'overload',
        'unsafe_operation',
      ]);

  @override
  Future<void> triggerScenario(String sessionId, String event) =>
      _delay<void>(null);
}
