import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:app/core/api/data_providers.dart';
import 'package:app/core/api/providers.dart';
import 'package:app/core/models/models.dart';
import 'package:app/l10n/app_localizations.dart';
import 'package:app/ui/theme.dart';
import 'package:app/ui/widgets/big_button.dart';

/// A5 — pre-start checklist with critical-defect gating (E12–E14).
class PreStartScreen extends ConsumerStatefulWidget {
  const PreStartScreen({super.key, required this.sessionId});

  final String sessionId;

  @override
  ConsumerState<PreStartScreen> createState() => _PreStartScreenState();
}

class _PreStartScreenState extends ConsumerState<PreStartScreen> {
  final Map<String, String> _status = {};
  bool _initialized = false;

  void _ensureInit(Checklist c) {
    if (_initialized) return;
    for (final s in c.sections) {
      for (final i in s.items) {
        _status[i.id] = i.status;
      }
    }
    _initialized = true;
  }

  void _set(String id, String status) {
    setState(() => _status[id] = status);
    // Best-effort persist to the backend (E13).
    ref
        .read(apiClientProvider)
        .updateChecklistItem(widget.sessionId, id, status: status);
  }

  void _snack(String m) =>
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(m)));

  Future<void> _complete(Checklist c) async {
    final t = AppLocalizations.of(context)!;
    final items = [for (final s in c.sections) ...s.items];
    final criticalDefects =
        items.where((i) => i.critical && _status[i.id] == 'defect');
    final unanswered =
        items.where((i) => (_status[i.id] ?? 'pending') == 'pending');

    if (criticalDefects.isNotEmpty) {
      _snack(t.checklist_complete_blocked);
      return;
    }
    if (unanswered.isNotEmpty) {
      _snack(t.checklist_answer_all);
      return;
    }
    await ref.read(apiClientProvider).completeChecklist(widget.sessionId);
    if (mounted) context.go('/session/${widget.sessionId}/briefing');
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context)!;
    final async = ref.watch(checklistProvider(widget.sessionId));

    return Scaffold(
      appBar: AppBar(title: Text(t.checklist_title)),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('$e')),
        data: (c) {
          _ensureInit(c);
          return Column(
            children: [
              Padding(
                padding: const EdgeInsets.all(8),
                child: Text(
                    '${t.checklist_based_on}: ${c.standardRefs.join(", ")}',
                    style: Theme.of(context).textTheme.bodySmall),
              ),
              Expanded(
                child: ListView(
                  children: [
                    for (final section in c.sections) ...[
                      Padding(
                        padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
                        child: Text(section.title,
                            style: Theme.of(context).textTheme.titleMedium),
                      ),
                      for (final item in section.items) _itemTile(item),
                    ],
                  ],
                ),
              ),
              Padding(
                padding: const EdgeInsets.all(12),
                child: BigButton(
                  label: t.action_complete,
                  icon: Icons.check,
                  onPressed: () => _complete(c),
                ),
              ),
            ],
          );
        },
      ),
    );
  }

  Widget _itemTile(ChecklistItem item) {
    final t = AppLocalizations.of(context)!;
    final status = _status[item.id] ?? 'pending';
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                    child:
                        Text(item.text, style: const TextStyle(fontSize: 16))),
                if (item.critical)
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(
                        color: AppTheme.critical,
                        borderRadius: BorderRadius.circular(4)),
                    child: Text(t.chk_critical,
                        style: const TextStyle(
                            color: Colors.white,
                            fontSize: 12,
                            fontWeight: FontWeight.bold)),
                  ),
              ],
            ),
            const SizedBox(height: 8),
            SegmentedButton<String>(
              emptySelectionAllowed: true,
              segments: [
                ButtonSegment(
                    value: 'ok',
                    label: Text(t.chk_ok),
                    icon: const Icon(Icons.check)),
                ButtonSegment(
                    value: 'defect',
                    label: Text(t.chk_defect),
                    icon: const Icon(Icons.warning)),
                ButtonSegment(value: 'na', label: Text(t.chk_na)),
              ],
              selected: const {'ok', 'defect', 'na'}.contains(status)
                  ? {status}
                  : <String>{},
              onSelectionChanged: (s) => _set(item.id, s.first),
            ),
          ],
        ),
      ),
    );
  }
}
