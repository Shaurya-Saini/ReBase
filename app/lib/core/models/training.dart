/// CONTRACT §4 TrainingModule.
class TrainingStep {
  const TrainingStep({required this.kind, required this.content, this.url});

  final String kind; // text | video | tip
  final String content;
  final String? url;

  factory TrainingStep.fromJson(Map<String, dynamic> j) => TrainingStep(
        kind: j['kind'] as String,
        content: j['content'] as String,
        url: j['url'] as String?,
      );
}

class QuizQuestion {
  const QuizQuestion({
    required this.q,
    required this.options,
    required this.answerIndex,
  });

  final String q;
  final List<String> options;
  final int answerIndex;

  factory QuizQuestion.fromJson(Map<String, dynamic> j) => QuizQuestion(
        q: j['q'] as String,
        options: (j['options'] as List).map((e) => e as String).toList(),
        answerIndex: (j['answer_index'] as num).toInt(),
      );
}

class TrainingModule {
  const TrainingModule({
    required this.id,
    required this.machineType,
    required this.level,
    required this.title,
    required this.durationMin,
    required this.steps,
    required this.quiz,
  });

  final String id;
  final String machineType;
  final String level; // Experience
  final String title;
  final int durationMin;
  final List<TrainingStep> steps;
  final List<QuizQuestion> quiz;

  factory TrainingModule.fromJson(Map<String, dynamic> j) => TrainingModule(
        id: j['id'] as String,
        machineType: j['machine_type'] as String,
        level: j['level'] as String,
        title: j['title'] as String,
        durationMin: (j['duration_min'] as num).toInt(),
        steps: (j['steps'] as List)
            .map((e) => TrainingStep.fromJson(e as Map<String, dynamic>))
            .toList(),
        quiz: (j['quiz'] as List)
            .map((e) => QuizQuestion.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}
