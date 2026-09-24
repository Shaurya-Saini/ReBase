import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:app/core/api/api_error.dart';
import 'package:app/core/api/data_providers.dart';
import 'package:app/core/api/providers.dart';
import 'package:app/core/models/models.dart';
import 'package:app/l10n/app_localizations.dart';
import 'package:app/ui/theme.dart';
import 'package:app/ui/widgets/big_button.dart';

/// A18 — Training Hub (CONTRACT v2.3). Home = personalized plan (E28) with
/// streak/progress + reason chips; tap a module → steps + quiz (E29) → server
/// grades (E30) with explanations. Content localized via Accept-Language.
class TrainingHubScreen extends ConsumerWidget {
  const TrainingHubScreen({
    super.key,
    required this.operatorId,
    this.machineType = 'excavator',
  });

  final String operatorId;
  final String machineType;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final t = AppLocalizations.of(context)!;
    final async = ref.watch(trainingPlanProvider(operatorId));

    return Scaffold(
      appBar: AppBar(title: Text(t.nav_training)),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('$e')),
        data: (plan) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            _progress(context, plan.progress, plan.totalMinutes),
            const SizedBox(height: 8),
            ...plan.items.map((item) => _itemCard(context, ref, item)),
            if (plan.items.isEmpty)
              const Padding(
                padding: EdgeInsets.all(24),
                child: Center(child: Text('All caught up ✓')),
              ),
          ],
        ),
      ),
    );
  }

  Widget _progress(BuildContext context, TrainingProgress p, int totalMin) {
    Widget stat(IconData i, String v, Color c) => Column(children: [
          Icon(i, color: c, size: 26),
          const SizedBox(height: 2),
          Text(v,
              style:
                  const TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
        ]);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            stat(
                Icons.local_fire_department, '${p.streakDays}', AppTheme.amber),
            stat(Icons.verified, '${p.modulesPassed}', AppTheme.green),
            stat(Icons.percent, '${p.avgScorePct}', AppTheme.offWhite),
            stat(Icons.timer, '$totalMin', AppTheme.muted),
          ],
        ),
      ),
    );
  }

  Widget _itemCard(BuildContext context, WidgetRef ref, PlanItem item) {
    final done = item.status == 'done';
    return Card(
      child: InkWell(
        onTap: () async {
          await Navigator.of(context).push(MaterialPageRoute(
            builder: (_) =>
                _ModuleScreen(moduleId: item.moduleId, operatorId: operatorId),
          ));
          ref.invalidate(trainingPlanProvider(operatorId)); // refresh after
        },
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(children: [
                Icon(done ? Icons.check_circle : Icons.circle_outlined,
                    color: done ? AppTheme.green : AppTheme.muted, size: 26),
                const SizedBox(width: 10),
                Expanded(
                    child: Text(item.title,
                        style: const TextStyle(
                            fontSize: 17, fontWeight: FontWeight.w700))),
                const Icon(Icons.chevron_right, color: AppTheme.muted),
              ]),
              const SizedBox(height: 8),
              Wrap(spacing: 6, runSpacing: 4, children: [
                _chip(Icons.timer, '${item.durationMin} min'),
                _chip(Icons.precision_manufacturing, item.machineType),
                _chip(Icons.school, item.level),
                if (item.lastResult != null)
                  _chip(Icons.history,
                      'last ${item.lastResult!.score}/${item.lastResult!.total}'),
              ]),
              ...item.reasons.map((r) => Padding(
                    padding: const EdgeInsets.only(top: 6),
                    child: Row(children: [
                      Icon(_reasonIcon(r.code),
                          size: 16, color: AppTheme.amber),
                      const SizedBox(width: 6),
                      Expanded(
                          child: Text(r.text,
                              style: const TextStyle(fontSize: 13))),
                    ]),
                  )),
            ],
          ),
        ),
      ),
    );
  }

  Widget _chip(IconData icon, String label) => Chip(
        avatar: Icon(icon, size: 16, color: AppTheme.amber),
        label: Text(label, style: const TextStyle(fontSize: 12)),
        backgroundColor: AppTheme.graphite,
        side: const BorderSide(color: AppTheme.graphiteLight),
        visualDensity: VisualDensity.compact,
      );

  IconData _reasonIcon(String code) => switch (code) {
        'recent_alert' => Icons.warning_amber,
        'job_hazard' => Icons.dangerous,
        'retake' => Icons.replay,
        'assigned' => Icons.assignment,
        'new_machine' => Icons.fiber_new,
        'level_up' => Icons.trending_up,
        'keep_fresh' => Icons.refresh,
        _ => Icons.info,
      };
}

/// Module: steps + quiz (E29) → server-graded result (E30).
class _ModuleScreen extends ConsumerStatefulWidget {
  const _ModuleScreen({required this.moduleId, required this.operatorId});
  final String moduleId;
  final String operatorId;

  @override
  ConsumerState<_ModuleScreen> createState() => _ModuleScreenState();
}

class _ModuleScreenState extends ConsumerState<_ModuleScreen> {
  final Map<int, int> _answers = {};
  QuizResult? _result;
  bool _busy = false;

  Future<void> _submit(TrainingModule m) async {
    setState(() => _busy = true);
    try {
      final answers =
          List<int?>.generate(m.quiz.length, (i) => _answers[i]); // null = skip
      final r = await ref
          .read(apiClientProvider)
          .submitQuiz(m.id, widget.operatorId, answers);
      if (mounted) setState(() => _result = r);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(SnackBar(
            content: Text(
                BackendError.from(e)?.message ?? 'Could not submit quiz')));
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context)!;
    final async = ref.watch(trainingModuleByIdProvider(widget.moduleId));

    return Scaffold(
      appBar: AppBar(title: Text(async.asData?.value.title ?? t.nav_training)),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('$e')),
        data: (m) => ListView(
          padding: const EdgeInsets.all(16),
          children: _result == null
              ? _lesson(context, t, m)
              : _resultView(context, t, m),
        ),
      ),
    );
  }

  List<Widget> _lesson(
      BuildContext context, AppLocalizations t, TrainingModule m) {
    return [
      ...m.steps.map((s) => Card(
            color:
                s.kind == 'tip' ? AppTheme.amber.withValues(alpha: 0.12) : null,
            child: ListTile(
              leading: Icon(s.kind == 'tip' ? Icons.lightbulb : Icons.article,
                  color: AppTheme.amber),
              title: Text(s.content, style: const TextStyle(fontSize: 16)),
            ),
          )),
      if (m.quiz.isNotEmpty) ...[
        const SizedBox(height: 12),
        Text(t.training_quiz, style: Theme.of(context).textTheme.titleLarge),
        const SizedBox(height: 8),
        ...m.quiz.asMap().entries.map((e) => _question(e.key, e.value)),
        const SizedBox(height: 8),
        BigButton(
          label: t.action_submit,
          icon: Icons.check,
          onPressed: _busy ? null : () => _submit(m),
        ),
      ],
    ];
  }

  Widget _question(int index, QuizQuestion q) => Card(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('${index + 1}. ${q.q}',
                  style: const TextStyle(
                      fontSize: 16, fontWeight: FontWeight.w700)),
              ...q.options.asMap().entries.map((o) => RadioListTile<int>(
                    contentPadding: EdgeInsets.zero,
                    dense: true,
                    value: o.key,
                    groupValue: _answers[index],
                    onChanged: (v) => setState(() => _answers[index] = v!),
                    title: Text(o.value),
                  )),
            ],
          ),
        ),
      );

  List<Widget> _resultView(
      BuildContext context, AppLocalizations t, TrainingModule m) {
    final r = _result!;
    return [
      Card(
        color:
            (r.passed ? AppTheme.green : AppTheme.red).withValues(alpha: 0.15),
        child: ListTile(
          leading: Icon(r.passed ? Icons.emoji_events : Icons.cancel,
              color: r.passed ? AppTheme.green : AppTheme.red, size: 32),
          title: Text('${t.training_result}: ${r.score} / ${r.total}',
              style:
                  const TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
          subtitle: Text(r.passed ? 'Passed' : 'Not passed'),
        ),
      ),
      const SizedBox(height: 8),
      ...r.results.map((qr) {
        final q = qr.index < m.quiz.length ? m.quiz[qr.index] : null;
        return Card(
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(children: [
                  Icon(qr.correct ? Icons.check_circle : Icons.cancel,
                      color: qr.correct ? AppTheme.green : AppTheme.red),
                  const SizedBox(width: 8),
                  Expanded(
                      child: Text('${qr.index + 1}. ${q?.q ?? ''}',
                          style: const TextStyle(fontWeight: FontWeight.w700))),
                ]),
                if (q != null) ...[
                  const SizedBox(height: 4),
                  Text('✓ ${q.options[qr.correctIndex]}',
                      style: const TextStyle(color: AppTheme.green)),
                  if (!qr.correct && qr.chosen != null)
                    Text('✗ ${q.options[qr.chosen!]}',
                        style: const TextStyle(color: AppTheme.red)),
                ],
                const SizedBox(height: 4),
                Text(qr.explanation, style: const TextStyle(fontSize: 13)),
                if (qr.source != null)
                  Padding(
                    padding: const EdgeInsets.only(top: 4),
                    child: Text('§ ${qr.source!.section}',
                        style: Theme.of(context).textTheme.bodySmall),
                  ),
              ],
            ),
          ),
        );
      }),
      const SizedBox(height: 12),
      BigButton(
        label: t.action_complete,
        icon: Icons.done,
        onPressed: () => Navigator.of(context).pop(),
      ),
    ];
  }
}
