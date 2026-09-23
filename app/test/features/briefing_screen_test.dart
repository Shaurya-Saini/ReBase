import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:app/core/api/mock_api_client.dart';
import 'package:app/core/api/providers.dart';
import 'package:app/features/session/briefing_screen.dart';
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
  testWidgets('shows briefing summaries, hazards and start button',
      (tester) async {
    await tester.pumpWidget(_wrap(const BriefingScreen(sessionId: 'ses_001')));
    await tester.pumpAndSettle();

    expect(find.textContaining('20t excavator'), findsOneWidget);
    expect(find.textContaining('Overhead power line'), findsOneWidget);
    expect(find.text('Start work'), findsOneWidget);
  });
}
