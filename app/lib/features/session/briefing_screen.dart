import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:app/core/api/data_providers.dart';
import 'package:app/core/lang.dart';
import 'package:app/core/locale.dart';
import 'package:app/core/models/models.dart';
import 'package:app/core/tts.dart';
import 'package:app/l10n/app_localizations.dart';
import 'package:app/ui/theme.dart';
import 'package:app/ui/widgets/big_button.dart';

/// A6 — operational briefing (E15) with on-device read-aloud.
class BriefingScreen extends ConsumerWidget {
  const BriefingScreen({super.key, required this.sessionId});

  final String sessionId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(context)!;
    final lang = contractLang(ref.watch(localeProvider).languageCode);
    final async =
        ref.watch(briefingProvider((sessionId: sessionId, lang: lang)));

    return Scaffold(
      appBar: AppBar(
        title: Text(t.briefing_title),
        actions: [
          async.maybeWhen(
            data: (b) => IconButton(
              icon: const Icon(Icons.volume_up),
              tooltip: 'Read aloud',
              onPressed: () => ref.read(ttsProvider).speak(_speech(b), b.lang),
            ),
            orElse: () => const SizedBox.shrink(),
          ),
        ],
      ),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('$e')),
        data: (b) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _section(context, Icons.precision_manufacturing, 'Machine',
                b.machineSummary),
            _section(context, Icons.work, 'Job', b.jobSummary),
            if (b.estimatedHours != null)
              _section(context, Icons.timer, t.job_estimate,
                  '${b.estimatedHours!.toStringAsFixed(1)} h'),
            _listSection(context, Icons.warning_amber, 'Hazards', b.hazards,
                AppTheme.warning),
            _listSection(
                context, Icons.info, 'Reminders', b.reminders, AppTheme.info),
            const SizedBox(height: 16),
            BigButton(
              label: t.action_start_work,
              icon: Icons.play_arrow,
              onPressed: () => context.go('/session/$sessionId/live'),
            ),
          ],
        ),
      ),
    );
  }

  String _speech(Briefing b) =>
      '${b.machineSummary}. ${b.jobSummary}. Hazards: ${b.hazards.join(", ")}. ${b.reminders.join(". ")}';

  Widget _section(
          BuildContext context, IconData icon, String title, String body) =>
      Card(
        child: ListTile(
          leading: Icon(icon),
          title: Text(title),
          subtitle: Text(body, style: const TextStyle(fontSize: 16)),
        ),
      );

  Widget _listSection(BuildContext context, IconData icon, String title,
          List<String> items, Color color) =>
      Card(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(children: [
                Icon(icon, color: color),
                const SizedBox(width: 8),
                Text(title, style: Theme.of(context).textTheme.titleMedium),
              ]),
              ...items.map((h) => Padding(
                    padding: const EdgeInsets.only(left: 32, top: 4),
                    child: Text('• $h', style: const TextStyle(fontSize: 15)),
                  )),
            ],
          ),
        ),
      );
}
