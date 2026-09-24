import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:app/core/api/api_client.dart';
import 'package:app/core/api/http_api_client.dart';
import 'package:app/core/api/mock_api_client.dart';
import 'package:app/core/config.dart';
import 'package:app/core/lang.dart';
import 'package:app/core/locale.dart';

/// The single client every screen reads. Mock or real, chosen at build time.
/// For the real client we pass the operator's language as `Accept-Language` so
/// the backend returns translated seeded/checklist text (CONTRACT v2.2). The
/// client is rebuilt when the language changes, so content re-fetches in the
/// new language.
final apiClientProvider = Provider<ApiClient>((ref) {
  if (AppConfig.useMock) return MockApiClient();
  final lang = contractLang(ref.watch(localeProvider).languageCode);
  return HttpApiClient(AppConfig.apiBase, lang: lang);
});
