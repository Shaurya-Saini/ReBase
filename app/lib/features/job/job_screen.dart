import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:app/core/api/api_client.dart';
import 'package:app/core/api/api_error.dart';
import 'package:app/core/api/data_providers.dart';
import 'package:app/core/api/providers.dart';
import 'package:app/core/models/models.dart';
import 'package:app/l10n/app_localizations.dart';
import 'package:app/ui/widgets/big_button.dart';
import 'package:app/ui/widgets/status_card.dart';

/// A4 — job detail + XGBoost estimate, with "start session" (E7, E8, E10).
class JobScreen extends ConsumerWidget {
  const JobScreen({super.key, required this.jobId, this.machineId});

  final String jobId;
  final String? machineId; // from the assignment (E5); resolved by type if null

  Future<void> _start(BuildContext context, WidgetRef ref, Job job) async {
    final api = ref.read(apiClientProvider);
    final op = ref.read(selectedOperatorProvider);
    try {
      var mId = machineId;
      if (mId == null) {
        final machines = await api.machines();
        mId = machines
            .firstWhere((m) => m.type == job.machineType,
                orElse: () => machines.first)
            .id;
      }
      final session = await api.createSession(
        operatorId: op?.id ?? 'op_001',
        machineId: mId,
        jobId: job.id,
      );
      if (context.mounted) context.push('/session/${session.id}/pre-start');
    } on SessionConflict catch (c) {
      // A session is already open — resume it (demo: move in/out freely).
      final id = c.existingSessionId;
      if (id == null) return;
      final s = await api.session(id);
      if (!context.mounted) return;
      context.push(switch (s.state) {
        'active' => '/session/${s.id}/live',
        'briefing' => '/session/${s.id}/briefing',
        _ => '/session/${s.id}/pre-start',
      });
    } catch (e) {
      // Backend rejection (REST_REQUIRED, MACHINE_TYPE_MISMATCH, …).
      if (!context.mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
          content: Text(
              BackendError.from(e)?.message ?? 'Could not start session')));
    }
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(context)!;
    final jobAsync = ref.watch(jobProvider(jobId));
    final estimateAsync = ref.watch(estimateProvider(jobId));

    return Scaffold(
      appBar: AppBar(title: Text(t.job_title)),
      body: jobAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('$e')),
        data: (job) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(job.title, style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 4),
            Text('${job.site} · ${job.machineType}',
                style: Theme.of(context).textTheme.titleMedium),
            const SizedBox(height: 12),
            Row(children: [
              Expanded(
                  child: StatusCard(
                      title: t.job_planned,
                      value: '${job.plannedHours.toStringAsFixed(1)} h',
                      icon: Icons.schedule)),
              Expanded(
                  child: StatusCard(
                      title: t.common_status,
                      value: job.status,
                      icon: Icons.flag)),
            ]),
            const SizedBox(height: 12),
            estimateAsync.when(
              loading: () => const Center(
                  child: Padding(
                      padding: EdgeInsets.all(16),
                      child: CircularProgressIndicator())),
              error: (e, _) => Text('$e'),
              data: (est) => _estimateCard(context, t, est),
            ),
            const SizedBox(height: 24),
            BigButton(
              label: t.action_start_session,
              icon: Icons.play_arrow,
              onPressed: () => _start(context, ref, job),
            ),
          ],
        ),
      ),
    );
  }

  Widget _estimateCard(BuildContext context, AppLocalizations t, Estimate est) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(t.job_estimate, style: Theme.of(context).textTheme.titleLarge),
            const SizedBox(height: 8),
            Text('${est.estimatedHours.toStringAsFixed(1)} h',
                style: Theme.of(context).textTheme.displaySmall),
            Text(
                'range ${est.rangeHours.first.toStringAsFixed(1)}–${est.rangeHours.last.toStringAsFixed(1)} h'),
            const Divider(height: 24),
            ...est.factors.map((f) {
              final up = f.effectPct >= 0;
              return ListTile(
                dense: true,
                contentPadding: EdgeInsets.zero,
                leading: Icon(up ? Icons.trending_up : Icons.trending_down,
                    color: up ? Colors.orangeAccent : Colors.greenAccent),
                title: Text(f.name),
                subtitle: f.note == null ? null : Text(f.note!),
                trailing: Text('${up ? '+' : ''}${f.effectPct}%'),
              );
            }),
            if (est.projectCompletionDate != null) ...[
              const Divider(height: 24),
              Text('${t.job_project_completion}: ${est.projectCompletionDate}'),
            ],
          ],
        ),
      ),
    );
  }
}
