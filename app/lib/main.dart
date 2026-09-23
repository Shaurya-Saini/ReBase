import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:app/core/locale.dart';
import 'package:app/l10n/app_localizations.dart';
import 'package:app/ui/router.dart';
import 'package:app/ui/theme.dart';

void main() => runApp(const ProviderScope(child: ReBaseApp()));

class ReBaseApp extends ConsumerWidget {
  const ReBaseApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final locale = ref.watch(localeProvider);
    return MaterialApp.router(
      title: 'ReBase',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.dark(),
      routerConfig: buildRouter(),
      locale: locale,
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: const [
        AppLocalizations.delegate,
        GlobalMaterialLocalizations.delegate,
        GlobalWidgetsLocalizations.delegate,
        GlobalCupertinoLocalizations.delegate,
      ],
    );
  }
}
