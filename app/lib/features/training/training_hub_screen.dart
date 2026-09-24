import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:video_player/video_player.dart';

import 'package:app/core/api/data_providers.dart';
import 'package:app/core/api/providers.dart';
import 'package:app/core/config.dart';
import 'package:app/core/models/models.dart';
import 'package:app/l10n/app_localizations.dart';
import 'package:app/ui/theme.dart';
import 'package:app/ui/widgets/big_button.dart';

/// A18 — pre-shift Training Hub (E26/E27). Shows B's module (text/tip/video
/// steps + quiz) for the operator's machine, in the selected language
/// (Accept-Language sent by the API client). Video lessons play in-app.
class TrainingHubScreen extends ConsumerStatefulWidget {
  const TrainingHubScreen({
    super.key,
    required this.operatorId,
    required this.machineType,
  });

  final String operatorId;
  final String machineType;

  @override
  ConsumerState<TrainingHubScreen> createState() => _TrainingHubScreenState();
}

class _TrainingHubScreenState extends ConsumerState<TrainingHubScreen> {
  final Map<int, int> _answers = {}; // question index -> chosen option
  int? _score;

  Future<void> _submit(TrainingModule m) async {
    var score = 0;
    for (var i = 0; i < m.quiz.length; i++) {
      if (_answers[i] == m.quiz[i].answerIndex) score++;
    }
    await ref
        .read(apiClientProvider)
        .completeTraining(m.id, operatorId: widget.operatorId, score: score);
    if (mounted) setState(() => _score = score);
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context)!;
    final async = ref.watch(trainingModuleProvider(
        (operatorId: widget.operatorId, machineType: widget.machineType)));

    return Scaffold(
      appBar: AppBar(title: Text(t.nav_training)),
      body: async.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('$e')),
        data: (m) => ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(m.title, style: Theme.of(context).textTheme.headlineSmall),
            const SizedBox(height: 4),
            Row(children: [
              _chip(Icons.timer, '${m.durationMin} min'),
              const SizedBox(width: 8),
              _chip(Icons.school, m.level),
            ]),
            const SizedBox(height: 16),
            ...m.steps.map(_step),
            if (m.quiz.isNotEmpty) ...[
              const SizedBox(height: 16),
              Text(t.training_quiz,
                  style: Theme.of(context).textTheme.titleLarge),
              const SizedBox(height: 8),
              ...m.quiz.asMap().entries.map((e) => _question(e.key, e.value)),
              const SizedBox(height: 8),
              if (_score == null)
                BigButton(
                  label: t.action_submit,
                  icon: Icons.check,
                  onPressed: _answers.length == m.quiz.length
                      ? () => _submit(m)
                      : null,
                )
              else
                Card(
                  color: AppTheme.green.withValues(alpha: 0.15),
                  child: ListTile(
                    leading: const Icon(Icons.emoji_events,
                        color: AppTheme.green, size: 32),
                    title: Text(
                        '${t.training_result}: $_score / ${m.quiz.length}',
                        style: const TextStyle(
                            fontSize: 20, fontWeight: FontWeight.w800)),
                  ),
                ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _chip(IconData icon, String label) => Chip(
        avatar: Icon(icon, size: 18, color: AppTheme.amber),
        label: Text(label),
        backgroundColor: AppTheme.graphite,
        side: const BorderSide(color: AppTheme.graphiteLight),
      );

  Widget _step(TrainingStep s) {
    switch (s.kind) {
      case 'video':
        return _VideoStep(url: s.url ?? '', caption: s.content);
      case 'tip':
        return Card(
          color: AppTheme.amber.withValues(alpha: 0.12),
          child: ListTile(
            leading: const Icon(Icons.lightbulb, color: AppTheme.amber),
            title: Text(s.content, style: const TextStyle(fontSize: 16)),
          ),
        );
      default: // text
        return Card(
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Text(s.content, style: const TextStyle(fontSize: 16)),
          ),
        );
    }
  }

  Widget _question(int index, QuizQuestion q) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('${index + 1}. ${q.q}',
                style:
                    const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
            ...q.options.asMap().entries.map((o) => RadioListTile<int>(
                  contentPadding: EdgeInsets.zero,
                  dense: true,
                  value: o.key,
                  groupValue: _answers[index],
                  onChanged: _score != null
                      ? null
                      : (v) => setState(() => _answers[index] = v!),
                  title: Text(o.value),
                )),
          ],
        ),
      ),
    );
  }
}

/// In-app player for a training video lesson (B's narrated MP4, A18/#20).
class _VideoStep extends StatefulWidget {
  const _VideoStep({required this.url, required this.caption});
  final String url;
  final String caption;

  @override
  State<_VideoStep> createState() => _VideoStepState();
}

class _VideoStepState extends State<_VideoStep> {
  VideoPlayerController? _c;
  bool _error = false;

  @override
  void initState() {
    super.initState();
    _init();
  }

  Future<void> _init() async {
    if (widget.url.isEmpty) {
      setState(() => _error = true);
      return;
    }
    final url = widget.url.startsWith('http')
        ? widget.url
        : '${AppConfig.apiBase}${widget.url.startsWith('/') ? '' : '/'}${widget.url}';
    final c = VideoPlayerController.networkUrl(Uri.parse(url));
    try {
      await c.initialize();
      if (mounted) setState(() => _c = c);
    } catch (_) {
      if (mounted) setState(() => _error = true);
    }
  }

  @override
  void dispose() {
    _c?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final c = _c;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(children: [
              const Icon(Icons.play_circle, color: AppTheme.amber),
              const SizedBox(width: 8),
              Expanded(
                  child: Text(widget.caption,
                      style: const TextStyle(fontWeight: FontWeight.w700))),
            ]),
            const SizedBox(height: 10),
            if (_error)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 16),
                child: Text('Video unavailable',
                    style: TextStyle(color: AppTheme.muted)),
              )
            else if (c == null)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 24),
                child: Center(child: CircularProgressIndicator()),
              )
            else
              Column(children: [
                AspectRatio(
                  aspectRatio:
                      c.value.aspectRatio == 0 ? 16 / 9 : c.value.aspectRatio,
                  child: VideoPlayer(c),
                ),
                VideoProgressIndicator(c, allowScrubbing: true),
                Row(mainAxisAlignment: MainAxisAlignment.center, children: [
                  IconButton(
                    iconSize: 40,
                    color: AppTheme.amber,
                    icon: Icon(c.value.isPlaying
                        ? Icons.pause_circle
                        : Icons.play_circle),
                    onPressed: () => setState(
                        () => c.value.isPlaying ? c.pause() : c.play()),
                  ),
                ]),
              ]),
          ],
        ),
      ),
    );
  }
}
