/// CONTRACT §4 AssistantRequest / AssistantAnswer.
class AnswerSource {
  const AnswerSource({required this.doc, required this.section});

  final String doc;
  final String section;

  factory AnswerSource.fromJson(Map<String, dynamic> j) => AnswerSource(
        doc: j['doc'] as String,
        section: j['section'] as String,
      );
}

class AssistantRequest {
  const AssistantRequest({
    required this.machineId,
    this.sessionId,
    required this.question,
    required this.lang,
  });

  final String machineId;
  final String? sessionId;
  final String question;
  final String lang;

  Map<String, dynamic> toJson() => {
        'machine_id': machineId,
        if (sessionId != null) 'session_id': sessionId,
        'question': question,
        'lang': lang,
      };
}

class AssistantAnswer {
  const AssistantAnswer({
    required this.answer,
    required this.lang,
    required this.sources,
  });

  final String answer;
  final String lang;
  final List<AnswerSource> sources;

  factory AssistantAnswer.fromJson(Map<String, dynamic> j) => AssistantAnswer(
        answer: j['answer'] as String,
        lang: j['lang'] as String,
        sources: (j['sources'] as List? ?? [])
            .map((e) => AnswerSource.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}
