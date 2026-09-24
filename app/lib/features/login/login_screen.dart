import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:app/core/api/data_providers.dart';
import 'package:app/core/api/providers.dart';
import 'package:app/core/locale.dart';
import 'package:app/core/models/models.dart';
import 'package:app/l10n/app_localizations.dart';
import 'package:app/ui/theme.dart';
import 'package:app/ui/widgets/big_button.dart';

/// A2 — operator picker + 4-digit PIN + live language switch.
class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

const _langChoices = {'en': 'English', 'hi': 'हिन्दी', 'ta': 'தமிழ்'};

class _LoginScreenState extends ConsumerState<LoginScreen> {
  Operator? _selected;
  final _pin = TextEditingController();
  bool _busy = false;

  @override
  void dispose() {
    _pin.dispose();
    super.dispose();
  }

  // Open PIN: any non-empty PIN is accepted (hackathon; not secure).
  bool get _canContinue => _selected != null && _pin.text.isNotEmpty && !_busy;

  void _pickLang(String code) =>
      ref.read(localeProvider.notifier).state = Locale(code);

  Future<void> _continue() async {
    final op = _selected!;
    setState(() => _busy = true);
    try {
      final loggedIn =
          await ref.read(apiClientProvider).login(op.id, _pin.text);
      ref.read(selectedOperatorProvider.notifier).state = loggedIn;
      if (mounted) context.go('/dashboard');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context)!;
    final operatorsAsync = ref.watch(operatorsProvider);
    final locale = ref.watch(localeProvider);

    return Scaffold(
      appBar: AppBar(
        title: Text(t.appTitle),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 12),
            child: DropdownButton<String>(
              value: locale.languageCode,
              underline: const SizedBox.shrink(),
              icon: const Icon(Icons.language),
              items: _langChoices.entries
                  .map((e) =>
                      DropdownMenuItem(value: e.key, child: Text(e.value)))
                  .toList(),
              onChanged: (v) {
                if (v != null) _pickLang(v);
              },
            ),
          ),
        ],
      ),
      body: operatorsAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('$e')),
        data: (operators) => Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(t.login_pick_operator,
                  style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 12),
              Expanded(
                child: ListView(
                  children: operators.map((op) {
                    final sel = _selected?.id == op.id;
                    return Card(
                      color: sel ? AppTheme.ok.withValues(alpha: 0.2) : null,
                      child: ListTile(
                        leading: Icon(sel ? Icons.check_circle : Icons.person,
                            color: sel ? AppTheme.ok : null, size: 32),
                        title:
                            Text(op.name, style: const TextStyle(fontSize: 20)),
                        subtitle: Text(op.experience.keys.join(', ')),
                        onTap: () => setState(() => _selected = op),
                      ),
                    );
                  }).toList(),
                ),
              ),
              const SizedBox(height: 12),
              TextField(
                controller: _pin,
                keyboardType: TextInputType.number,
                obscureText: true,
                maxLength: 4,
                inputFormatters: [FilteringTextInputFormatter.digitsOnly],
                onChanged: (_) => setState(() {}),
                decoration: InputDecoration(
                  labelText: t.login_pin,
                  border: const OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 8),
              BigButton(
                label: t.action_continue,
                icon: Icons.login,
                onPressed: _canContinue ? _continue : null,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
