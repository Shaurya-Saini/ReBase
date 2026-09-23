import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:app/core/api/providers.dart';
import 'package:app/core/lang.dart';
import 'package:app/core/locale.dart';
import 'package:app/core/models/models.dart';
import 'package:app/core/stt.dart';
import 'package:app/core/tts.dart';
import 'package:app/l10n/app_localizations.dart';

/// A11 (chat) + A10 (voice loop): ask the manual assistant by text or by
/// hold-to-talk; answers are grounded (RAG) with sources and can be read aloud.
class AssistantScreen extends ConsumerStatefulWidget {
  const AssistantScreen({super.key, this.machineId = 'mc_001'});

  final String machineId;

  @override
  ConsumerState<AssistantScreen> createState() => _AssistantScreenState();
}

class _Msg {
  _Msg.question(this.text)
      : isQuestion = true,
        answer = null;
  _Msg.answer(AssistantAnswer a)
      : isQuestion = false,
        answer = a,
        text = a.answer;

  final bool isQuestion;
  late final String text;
  final AssistantAnswer? answer;
}

class _AssistantScreenState extends ConsumerState<AssistantScreen> {
  final _controller = TextEditingController();
  final List<_Msg> _messages = [];
  bool _busy = false;
  bool _listening = false;

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _ask(String question, {bool speak = false}) async {
    final q = question.trim();
    if (q.isEmpty || _busy) return;
    setState(() {
      _messages.add(_Msg.question(q));
      _busy = true;
    });
    _controller.clear();
    try {
      final lang = contractLang(ref.read(localeProvider).languageCode);
      final ans = await ref.read(apiClientProvider).ask(
            AssistantRequest(
                machineId: widget.machineId, question: q, lang: lang),
          );
      if (!mounted) return;
      setState(() => _messages.add(_Msg.answer(ans)));
      if (speak) ref.read(ttsProvider).speak(ans.answer, ans.lang);
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Future<void> _startListening() async {
    final stt = ref.read(sttProvider);
    if (!await stt.init()) return;
    if (!mounted) return;
    setState(() => _listening = true);
    await stt.listen(
      localeId: sttLocaleId(ref.read(localeProvider).languageCode),
      onResult: (text) => _controller.text = text,
    );
  }

  Future<void> _stopListening() async {
    await ref.read(sttProvider).stop();
    if (mounted) setState(() => _listening = false);
    await _ask(_controller.text, speak: true);
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context)!;
    return Scaffold(
      appBar: AppBar(title: Text(t.assistant_title)),
      body: Column(
        children: [
          Expanded(
            child: _messages.isEmpty
                ? Center(child: Text(t.assistant_hint))
                : ListView(
                    padding: const EdgeInsets.all(12),
                    children: _messages.map(_bubble).toList(),
                  ),
          ),
          if (_busy) const LinearProgressIndicator(),
          _inputBar(t),
        ],
      ),
    );
  }

  Widget _bubble(_Msg m) {
    if (m.isQuestion) {
      return Align(
        alignment: Alignment.centerRight,
        child: Card(
          color: Theme.of(context).colorScheme.primary,
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Text(m.text,
                style: const TextStyle(color: Colors.black, fontSize: 16)),
          ),
        ),
      );
    }
    final a = m.answer!;
    return Align(
      alignment: Alignment.centerLeft,
      child: Card(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(a.answer, style: const TextStyle(fontSize: 16)),
              if (a.sources.isNotEmpty)
                Padding(
                  padding: const EdgeInsets.only(top: 6),
                  child: Text(
                    'Source: ${a.sources.map((s) => s.section).join(", ")}',
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ),
              Align(
                alignment: Alignment.centerRight,
                child: IconButton(
                  icon: const Icon(Icons.volume_up),
                  tooltip: 'Read aloud',
                  onPressed: () =>
                      ref.read(ttsProvider).speak(a.answer, a.lang),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _inputBar(AppLocalizations t) => Padding(
        padding: const EdgeInsets.all(8),
        child: Row(
          children: [
            GestureDetector(
              onLongPressStart: (_) => _startListening(),
              onLongPressEnd: (_) => _stopListening(),
              child: CircleAvatar(
                radius: 26,
                backgroundColor: _listening
                    ? Colors.red
                    : Theme.of(context).colorScheme.primary,
                child: const Icon(Icons.mic, color: Colors.black),
              ),
            ),
            const SizedBox(width: 8),
            Expanded(
              child: TextField(
                controller: _controller,
                textInputAction: TextInputAction.send,
                onSubmitted: _ask,
                decoration: InputDecoration(
                  hintText: t.assistant_hint,
                  border: const OutlineInputBorder(),
                ),
              ),
            ),
            IconButton(
              icon: const Icon(Icons.send),
              onPressed: _busy ? null : () => _ask(_controller.text),
            ),
          ],
        ),
      );
}
