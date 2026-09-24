import 'dart:typed_data';

import 'package:app/core/models/models.dart';

/// Thrown by [ApiClient.createSession] when the backend already has an open
/// session for the operator/machine (409). `existingSessionId` lets the app
/// resume it, so the demo can move in and out of a session without ending it.
class SessionConflict implements Exception {
  SessionConflict(this.existingSessionId);
  final String? existingSessionId;
}

/// The one interface every screen talks to (CONTRACT §6.1). One method per
/// endpoint E1–E27. `MockApiClient` and `HttpApiClient` implement it; the active
/// one is chosen by `apiClientProvider` via `USE_MOCK`.
abstract class ApiClient {
  Future<Operator> login(String operatorId, String pin); // E2
  Future<List<Operator>> operators(); // E3
  Future<Operator> operatorById(String id); // E4
  Future<List<Assignment>> assignments(String operatorId, {String range}); // E5
  Future<List<Machine>> machines(); // E6
  Future<Machine> machine(String id); // E6
  Future<Job> job(String id); // E7
  Future<Estimate> estimate(String jobId); // E8
  Future<Session> createSession({
    required String operatorId,
    required String machineId,
    required String jobId,
  }); // E10
  Future<Session> session(String id); // E11
  Future<Checklist> checklist(String sessionId); // E12
  Future<ChecklistItem> updateChecklistItem(
    String sessionId,
    String itemId, {
    required String status,
    String? note,
  }); // E13
  Future<Session> completeChecklist(String sessionId); // E14
  Future<Briefing> briefing(String sessionId, {String lang}); // E15
  Future<Session> startSession(String sessionId); // E16
  Future<SessionSummary> endSession(String sessionId); // E17
  Future<Alert> postAlert(String sessionId, AlertCreate alert); // E18
  Future<List<Alert>> alerts(String sessionId); // E19
  Future<Alert> ackAlert(String alertId); // E20
  Future<AssistantAnswer> ask(AssistantRequest req); // E23
  Future<Uint8List> tts(String text, String lang); // E24
  Future<String> translate(String text, String target); // E25
  Future<TrainingModule> nextTraining(
      String operatorId, String machineType); // E26
  Future<void> completeTraining(
    String moduleId, {
    required String operatorId,
    required int score,
  }); // E27
  Future<List<String>> simScenarios(); // E21 — demo control
  Future<void> triggerScenario(
      String sessionId, String event); // E22 — demo control
  Future<TrainingPlan> trainingPlan(String operatorId); // E28
  Future<TrainingModule> trainingModule(String moduleId); // E29
  Future<QuizResult> submitQuiz(
      String moduleId, String operatorId, List<int?> answers); // E30
}
