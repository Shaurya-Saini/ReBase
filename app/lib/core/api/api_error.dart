import 'package:dio/dio.dart';

/// Parses the backend error envelope `{"error": {"code", "message", ...}}`
/// (CONTRACT §1) from a thrown error, so screens can show it without importing
/// dio directly.
class BackendError {
  BackendError(this.code, this.message, this.data);

  final String? code;
  final String? message;
  final Map<String, dynamic>
      data; // the whole error object (items, session_id…)

  static BackendError? from(Object e) {
    if (e is DioException && e.response?.data is Map) {
      final err = (e.response!.data as Map)['error'];
      if (err is Map) {
        final m = err.cast<String, dynamic>();
        return BackendError(m['code'] as String?, m['message'] as String?, m);
      }
    }
    return null;
  }
}
