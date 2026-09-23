import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:app/core/api/mock_api_client.dart';
import 'package:app/core/api/providers.dart';
import 'package:app/features/job/job_screen.dart';
import 'package:app/l10n/app_localizations.dart';

Widget _wrap(Widget child) => ProviderScope(
      overrides: [apiClientProvider.overrideWithValue(MockApiClient())],
      child: MaterialApp(
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: child,
      ),
    );

void main() {
  testWidgets('shows job detail + estimate with a range', (tester) async {
    await tester.pumpWidget(_wrap(const JobScreen(jobId: 'job_001')));
    await tester.pumpAndSettle();

    expect(find.textContaining('Trench excavation'), findsOneWidget);
    expect(find.text('6.8 h'), findsOneWidget); // estimatedHours
    expect(find.textContaining('range 5.9'), findsOneWidget);
    expect(find.text('weather'), findsOneWidget); // a factor
  });
}
