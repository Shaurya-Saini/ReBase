import 'package:app/core/models/assistant.dart' show AnswerSource;

/// CONTRACT §4 v2.3 — TrainingPlan (E28), QuizResult (E30).
class TrainingProgress {
  const TrainingProgress({
    required this.attempts,
    required this.modulesPassed,
    required this.avgScorePct,
    required this.streakDays,
  });

  final int attempts;
  final int modulesPassed;
  final int avgScorePct;
  final int streakDays;

  factory TrainingProgress.fromJson(Map<String, dynamic> j) => TrainingProgress(
        attempts: (j['attempts'] as num?)?.toInt() ?? 0,
        modulesPassed: (j['modules_passed'] as num?)?.toInt() ?? 0,
        avgScorePct: (j['avg_score_pct'] as num?)?.toInt() ?? 0,
        streakDays: (j['streak_days'] as num?)?.toInt() ?? 0,
      );
}

class PlanReason {
  const PlanReason({required this.code, required this.text});
  final String code; // recent_alert | job_hazard | retake | assigned | ...
  final String text; // localized, ready to show

  factory PlanReason.fromJson(Map<String, dynamic> j) =>
      PlanReason(code: j['code'] as String, text: j['text'] as String);
}

class LastResult {
  const LastResult({required this.score, required this.total, this.at});
  final int score;
  final int total;
  final String? at;

  factory LastResult.fromJson(Map<String, dynamic> j) => LastResult(
        score: (j['score'] as num).toInt(),
        total: (j['total'] as num).toInt(),
        at: j['at'] as String?,
      );
}

class PlanItem {
  const PlanItem({
    required this.moduleId,
    required this.title,
    required this.machineType,
    required this.level,
    required this.durationMin,
    required this.priority,
    required this.status,
    required this.reasons,
    this.lastResult,
  });

  final String moduleId;
  final String title;
  final String machineType;
  final String level;
  final int durationMin;
  final int priority;
  final String status; // todo | done
  final List<PlanReason> reasons;
  final LastResult? lastResult;

  factory PlanItem.fromJson(Map<String, dynamic> j) => PlanItem(
        moduleId: j['module_id'] as String,
        title: j['title'] as String,
        machineType: j['machine_type'] as String,
        level: j['level'] as String,
        durationMin: (j['duration_min'] as num).toInt(),
        priority: (j['priority'] as num).toInt(),
        status: j['status'] as String,
        reasons: (j['reasons'] as List? ?? [])
            .map((e) => PlanReason.fromJson(e as Map<String, dynamic>))
            .toList(),
        lastResult: j['last_result'] == null
            ? null
            : LastResult.fromJson(j['last_result'] as Map<String, dynamic>),
      );
}

class TrainingPlan {
  const TrainingPlan({
    required this.operatorId,
    required this.date,
    required this.lang,
    required this.totalMinutes,
    required this.items,
    required this.progress,
  });

  final String operatorId;
  final String date;
  final String lang;
  final int totalMinutes;
  final List<PlanItem> items;
  final TrainingProgress progress;

  factory TrainingPlan.fromJson(Map<String, dynamic> j) => TrainingPlan(
        operatorId: j['operator_id'] as String,
        date: j['date'] as String,
        lang: j['lang'] as String,
        totalMinutes: (j['total_minutes'] as num?)?.toInt() ?? 0,
        items: (j['items'] as List? ?? [])
            .map((e) => PlanItem.fromJson(e as Map<String, dynamic>))
            .toList(),
        progress: TrainingProgress.fromJson(
            (j['progress'] as Map<String, dynamic>?) ?? const {}),
      );
}

class QuestionResult {
  const QuestionResult({
    required this.index,
    this.chosen,
    required this.correctIndex,
    required this.correct,
    required this.explanation,
    this.source,
  });

  final int index;
  final int? chosen;
  final int correctIndex;
  final bool correct;
  final String explanation;
  final AnswerSource? source;

  factory QuestionResult.fromJson(Map<String, dynamic> j) => QuestionResult(
        index: (j['index'] as num).toInt(),
        chosen: (j['chosen'] as num?)?.toInt(),
        correctIndex: (j['correct_index'] as num).toInt(),
        correct: j['correct'] as bool? ?? false,
        explanation: j['explanation'] as String? ?? '',
        source: j['source'] == null
            ? null
            : AnswerSource.fromJson(j['source'] as Map<String, dynamic>),
      );
}

class QuizResult {
  const QuizResult({
    required this.moduleId,
    required this.score,
    required this.total,
    required this.passed,
    required this.results,
  });

  final String moduleId;
  final int score;
  final int total;
  final bool passed;
  final List<QuestionResult> results;

  factory QuizResult.fromJson(Map<String, dynamic> j) => QuizResult(
        moduleId: j['module_id'] as String,
        score: (j['score'] as num).toInt(),
        total: (j['total'] as num).toInt(),
        passed: j['passed'] as bool? ?? false,
        results: (j['results'] as List? ?? [])
            .map((e) => QuestionResult.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}
