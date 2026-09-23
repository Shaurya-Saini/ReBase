import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:app/core/api/mock_api_client.dart';
import 'package:app/core/api/providers.dart';
import 'package:app/features/assistant/assistant_screen.dart';
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
  testWidgets('typing a question returns a grounded answer with a source',
      (tester) async {
    await tester.pumpWidget(_wrap(const AssistantScreen()));
    await tester.pump();

    await tester.enterText(
        find.byType(TextField), 'How do I switch to power mode?');
    await tester.tap(find.byIcon(Icons.send));
    await tester.pumpAndSettle();

    expect(find.textContaining('power mode'), findsWidgets);
    expect(find.textContaining('4.2 Operating modes'), findsOneWidget);
  });
}
