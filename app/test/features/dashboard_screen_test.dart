import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:app/core/api/data_providers.dart';
import 'package:app/core/api/mock_api_client.dart';
import 'package:app/core/api/mock_data.dart';
import 'package:app/core/api/providers.dart';
import 'package:app/features/dashboard/dashboard_screen.dart';
import 'package:app/l10n/app_localizations.dart';

Widget _wrap(Widget child) => ProviderScope(
      overrides: [
        apiClientProvider.overrideWithValue(MockApiClient()),
        selectedOperatorProvider.overrideWith((ref) => MockData.operator1()),
      ],
      child: MaterialApp(
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: child,
      ),
    );

void main() {
  testWidgets('shows hours, rest and today\'s assignment', (tester) async {
    await tester.pumpWidget(_wrap(const DashboardScreen()));
    await tester.pumpAndSettle();

    expect(find.text('3.5 h'), findsOneWidget); // hoursToday
    expect(find.textContaining('Trench excavation'), findsOneWidget);
  });
}
