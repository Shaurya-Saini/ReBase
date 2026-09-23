// Skeleton — routes on-device AlertDrafts (from rules + CV) to the backend
// incident log via E18 (POST /sessions/{id}/alerts).

import 'package:app/edge/telemetry_rules.dart' show AlertDraft;

/// TODO A8/A9: convert AlertDraft -> core `AlertCreate` and call
/// `apiClientProvider.postAlert(sessionId, alert)` (CONTRACT §6.1, E18).
class AlertDispatcher {
  AlertDispatcher(this.sessionId);

  final String sessionId;

  Future<void> dispatch(AlertDraft draft) async {
    // TODO: await apiClient.postAlert(sessionId, draft.toAlertCreate());
  }
}
