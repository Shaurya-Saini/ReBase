// Routes on-device AlertDrafts (from the rule engine + camera CV) to the backend
// incident log via E18 (POST /sessions/{id}/alerts).

import 'package:app/core/api/api_client.dart';
import 'package:app/core/models/models.dart';
import 'package:app/edge/telemetry_rules.dart' show AlertDraft;

class AlertDispatcher {
  AlertDispatcher(this._api, this.sessionId);

  final ApiClient _api;
  final String sessionId;

  /// Stamps the draft with a timestamp and posts it; returns the stored Alert.
  Future<Alert> dispatch(AlertDraft d) => _api.postAlert(
        sessionId,
        AlertCreate(
          type: d.type,
          source: d.source,
          severity: d.severity,
          message: d.message,
          ts: DateTime.now().toUtc().toIso8601String(),
        ),
      );
}
