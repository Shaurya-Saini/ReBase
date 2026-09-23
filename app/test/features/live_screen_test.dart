import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:app/core/api/mock_api_client.dart';
import 'package:app/core/api/providers.dart';
import 'package:app/core/api/ws_client.dart';
import 'package:app/core/models/models.dart';
import 'package:app/features/session/live_screen.dart';
import 'package:app/l10n/app_localizations.dart';
import 'package:app/ui/widgets/alert_banner.dart';

Widget _wrap(Widget child) => ProviderScope(
      overrides: [
        apiClientProvider.overrideWithValue(MockApiClient()),
        // No real telemetry timer in tests — the dev triggers drive the engine.
        telemetryStreamProvider
            .overrideWith((ref, id) => const Stream<Telemetry>.empty()),
      ],
      child: MaterialApp(
        localizationsDelegates: AppLocalizations.localizationsDelegates,
        supportedLocales: AppLocalizations.supportedLocales,
        home: child,
      ),
    );

void main() {
  testWidgets('firing a telemetry rule shows an alert banner + acks it',
      (tester) async {
    await tester.pumpWidget(_wrap(const LiveScreen(sessionId: 'ses_001')));
    await tester.pump();

    expect(find.byType(AlertBanner), findsNothing);

    await tester.tap(find.text('Seatbelt'));
    await tester.pumpAndSettle();

    expect(find.byType(AlertBanner), findsOneWidget);

    await tester.tap(find.text('ACK'));
    await tester.pumpAndSettle();

    expect(find.byType(AlertBanner), findsNothing);
  });

  testWidgets('camera CV trigger raises a drowsiness alert', (tester) async {
    await tester.pumpWidget(_wrap(const LiveScreen(sessionId: 'ses_001')));
    await tester.pump();

    await tester.tap(find.text('Drowsy (CV)'));
    // No telemetry set → gauges show a spinner (perpetual anim), so pump fixed
    // durations rather than pumpAndSettle.
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 200));

    expect(find.byType(AlertBanner), findsOneWidget);
  });
}
