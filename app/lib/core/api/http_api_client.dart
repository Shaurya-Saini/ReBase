import 'dart:typed_data';

import 'package:dio/dio.dart';

import 'package:app/core/api/api_client.dart';
import 'package:app/core/models/models.dart';

/// Real backend client for `USE_MOCK=false`. Verified against B's stubbed
/// endpoints. One-to-one with CONTRACT §3.
class HttpApiClient implements ApiClient {
  HttpApiClient(String baseUrl)
      : _dio = Dio(BaseOptions(
          baseUrl: baseUrl,
          connectTimeout: const Duration(seconds: 5),
          receiveTimeout: const Duration(seconds: 20),
        ));

  final Dio _dio;

  Map<String, dynamic> _m(Object? data) =>
      (data as Map).cast<String, dynamic>();

  List<Map<String, dynamic>> _l(Object? data) =>
      (data as List).map((e) => (e as Map).cast<String, dynamic>()).toList();

  @override
  Future<Operator> login(String operatorId, String pin) async =>
      Operator.fromJson(_m((await _dio.post('/auth/login',
              data: {'operator_id': operatorId, 'pin': pin}))
          .data));

  @override
  Future<List<Operator>> operators() async =>
      _l((await _dio.get('/operators')).data).map(Operator.fromJson).toList();

  @override
  Future<Operator> operatorById(String id) async =>
      Operator.fromJson(_m((await _dio.get('/operators/$id')).data));

  @override
  Future<List<Assignment>> assignments(String operatorId,
          {String range = 'day'}) async =>
      _l((await _dio.get('/operators/$operatorId/assignments',
                  queryParameters: {'range': range}))
              .data)
          .map(Assignment.fromJson)
          .toList();

  @override
  Future<List<Machine>> machines() async =>
      _l((await _dio.get('/machines')).data).map(Machine.fromJson).toList();

  @override
  Future<Machine> machine(String id) async =>
      Machine.fromJson(_m((await _dio.get('/machines/$id')).data));

  @override
  Future<Job> job(String id) async =>
      Job.fromJson(_m((await _dio.get('/jobs/$id')).data));

  @override
  Future<Estimate> estimate(String jobId) async =>
      Estimate.fromJson(_m((await _dio.get('/jobs/$jobId/estimate')).data));

  @override
  Future<Session> createSession({
    required String operatorId,
    required String machineId,
    required String jobId,
  }) async =>
      Session.fromJson(_m((await _dio.post('/sessions', data: {
        'operator_id': operatorId,
        'machine_id': machineId,
        'job_id': jobId,
      }))
          .data));

  @override
  Future<Session> session(String id) async =>
      Session.fromJson(_m((await _dio.get('/sessions/$id')).data));

  @override
  Future<Checklist> checklist(String sessionId) async => Checklist.fromJson(
      _m((await _dio.get('/sessions/$sessionId/checklist')).data));

  @override
  Future<ChecklistItem> updateChecklistItem(
    String sessionId,
    String itemId, {
    required String status,
    String? note,
  }) async =>
      ChecklistItem.fromJson(_m((await _dio.put(
              '/sessions/$sessionId/checklist/items/$itemId',
              data: {'status': status, if (note != null) 'note': note}))
          .data));

  @override
  Future<Session> completeChecklist(String sessionId) async => Session.fromJson(
      _m((await _dio.post('/sessions/$sessionId/checklist/complete')).data));

  @override
  Future<Briefing> briefing(String sessionId, {String lang = 'en-IN'}) async =>
      Briefing.fromJson(_m((await _dio.get('/sessions/$sessionId/briefing',
              queryParameters: {'lang': lang}))
          .data));

  @override
  Future<Session> startSession(String sessionId) async => Session.fromJson(
      _m((await _dio.post('/sessions/$sessionId/start')).data));

  @override
  Future<SessionSummary> endSession(String sessionId) async =>
      SessionSummary.fromJson(
          _m((await _dio.post('/sessions/$sessionId/end')).data));

  @override
  Future<Alert> postAlert(String sessionId, AlertCreate alert) async =>
      Alert.fromJson(_m(
          (await _dio.post('/sessions/$sessionId/alerts', data: alert.toJson()))
              .data));

  @override
  Future<List<Alert>> alerts(String sessionId) async =>
      _l((await _dio.get('/sessions/$sessionId/alerts')).data)
          .map(Alert.fromJson)
          .toList();

  @override
  Future<Alert> ackAlert(String alertId) async =>
      Alert.fromJson(_m((await _dio.post('/alerts/$alertId/ack')).data));

  @override
  Future<AssistantAnswer> ask(AssistantRequest req) async =>
      AssistantAnswer.fromJson(
          _m((await _dio.post('/assistant/ask', data: req.toJson())).data));

  @override
  Future<Uint8List> tts(String text, String lang) async {
    final r = await _dio.post('/voice/tts',
        data: {'text': text, 'lang': lang},
        options: Options(responseType: ResponseType.bytes));
    return Uint8List.fromList((r.data as List).cast<int>());
  }

  @override
  Future<String> translate(String text, String target) async =>
      _m((await _dio.post('/translate', data: {'text': text, 'target': target}))
          .data)['text'] as String;

  @override
  Future<TrainingModule> nextTraining(
          String operatorId, String machineType) async =>
      TrainingModule.fromJson(_m((await _dio.get(
              '/operators/$operatorId/training/next',
              queryParameters: {'machine_type': machineType}))
          .data));

  @override
  Future<void> completeTraining(
    String moduleId, {
    required String operatorId,
    required int score,
  }) async {
    await _dio.post('/training/$moduleId/complete',
        data: {'operator_id': operatorId, 'score': score});
  }
}
