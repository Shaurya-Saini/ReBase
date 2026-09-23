import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:app/core/api/api_client.dart';
import 'package:app/core/api/http_api_client.dart';
import 'package:app/core/api/mock_api_client.dart';
import 'package:app/core/config.dart';

/// The single client every screen reads. Mock or real, chosen at build time.
final apiClientProvider = Provider<ApiClient>((ref) =>
    AppConfig.useMock ? MockApiClient() : HttpApiClient(AppConfig.apiBase));
