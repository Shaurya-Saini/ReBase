import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:app/core/api/data_providers.dart';
import 'package:app/l10n/app_localizations.dart';
import 'package:app/ui/theme.dart';
import 'package:app/ui/widgets/status_card.dart';

/// A3 — unmounted dashboard: assignments (day/week/month) + hours & rest.
class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(context)!;
    final op = ref.watch(selectedOperatorProvider);

    if (op == null) {
      // Reached without logging in (e.g. deep link) — send back to login.
      return Scaffold(
        body: Center(
          child: FilledButton(
            onPressed: () => context.go('/'),
            child: Text(t.login_title),
          ),
        ),
      );
    }

    final range = ref.watch(rangeProvider);
    final assignmentsAsync =
        ref.watch(assignmentsProvider((operatorId: op.id, range: range)));

    return Scaffold(
      appBar: AppBar(
        title: Text(t.dashboard_title),
        actions: [
          IconButton(
            icon: const Icon(Icons.school),
            tooltip: t.nav_training,
            onPressed: () => context
                .go('/training?operatorId=${op.id}&machineType=excavator'),
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                Expanded(
                  child: StatusCard(
                    title: t.dashboard_hours,
                    value: '${op.hoursToday.toStringAsFixed(1)} h',
                    icon: Icons.timer,
                  ),
                ),
                Expanded(
                  child: StatusCard(
                    title: t.dashboard_rest,
                    value: _restLabel(t, op.rest.status),
                    icon: Icons.bedtime,
                    color: _restColor(op.rest.status),
                  ),
                ),
              ],
            ),
          ),
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 12),
            child: SegmentedButton<String>(
              segments: const [
                ButtonSegment(value: 'day', label: Text('Day')),
                ButtonSegment(value: 'week', label: Text('Week')),
                ButtonSegment(value: 'month', label: Text('Month')),
              ],
              selected: {range},
              onSelectionChanged: (s) =>
                  ref.read(rangeProvider.notifier).state = s.first,
            ),
          ),
          const SizedBox(height: 8),
          Expanded(
            child: assignmentsAsync.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(child: Text('$e')),
              data: (list) => list.isEmpty
                  ? const Center(child: Text('—'))
                  : ListView(
                      children: list
                          .map((a) => Card(
                                child: ListTile(
                                  leading:
                                      const Icon(Icons.assignment, size: 32),
                                  title: Text(a.job.title,
                                      style: const TextStyle(fontSize: 18)),
                                  subtitle: Text(
                                      '${a.job.site} · ${a.machine.model} · ${a.shift}'),
                                  trailing: const Icon(Icons.chevron_right),
                                  onTap: () => context.go('/job/${a.job.id}'),
                                ),
                              ))
                          .toList(),
                    ),
            ),
          ),
        ],
      ),
    );
  }
}

String _restLabel(AppLocalizations t, String status) => switch (status) {
      'ok' => t.rest_ok,
      'warning' => t.rest_warning,
      _ => t.rest_must,
    };

Color _restColor(String status) => switch (status) {
      'ok' => AppTheme.ok,
      'warning' => AppTheme.warning,
      _ => AppTheme.critical,
    };
