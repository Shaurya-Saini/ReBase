import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:app/core/api/mock_api_client.dart';
import 'package:app/core/api/providers.dart';
import 'package:app/features/login/login_screen.dart';
import 'package:app/l10n/app_localizations.dart';
import 'package:app/ui/widgets/big_button.dart';

Widget _wrap(Widget child) => ProviderScope(
      overrides: [apiClientProvider.overrideWithValue(MockApiClient())],
      child: MaterialApp(
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: child,
      ),
    );

void main() {
  testWidgets('lists operators from the API', (tester) async {
    await tester.pumpWidget(_wrap(const LoginScreen()));
    await tester.pumpAndSettle();
    expect(find.text('Ravi Kumar'), findsOneWidget);
    expect(find.text('Amit Singh'), findsOneWidget);
  });

  testWidgets('continue enables only after operator + 4-digit PIN',
      (tester) async {
    await tester.pumpWidget(_wrap(const LoginScreen()));
    await tester.pumpAndSettle();

    final btn = find.byType(BigButton);
    expect(btn, findsOneWidget);
    expect(tester.widget<BigButton>(btn).onPressed, isNull);

    await tester.tap(find.text('Ravi Kumar'));
    await tester.pump();
    await tester.enterText(find.byType(TextField), '1234');
    await tester.pump();

    expect(tester.widget<BigButton>(btn).onPressed, isNotNull);
  });
}
