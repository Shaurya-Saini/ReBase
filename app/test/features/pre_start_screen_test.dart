import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:app/core/api/mock_api_client.dart';
import 'package:app/core/api/providers.dart';
import 'package:app/features/session/pre_start_screen.dart';
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
  testWidgets('renders items and marks the critical one', (tester) async {
    await tester.pumpWidget(_wrap(const PreStartScreen(sessionId: 'ses_001')));
    await tester.pumpAndSettle();

    expect(find.text('Check hydraulic hoses for leaks'), findsOneWidget);
    expect(find.text('CRITICAL'), findsOneWidget);
  });

  testWidgets('a critical defect blocks completion', (tester) async {
    await tester.pumpWidget(_wrap(const PreStartScreen(sessionId: 'ses_001')));
    await tester.pumpAndSettle();

    // Mark the critical item (2nd 'Defect' segment) as a defect.
    await tester.tap(find.text('Defect').at(1));
    await tester.pumpAndSettle();

    await tester.tap(find.text('Complete'));
    await tester.pumpAndSettle();

    expect(find.text('Fix critical defects before starting'), findsOneWidget);
  });
}
