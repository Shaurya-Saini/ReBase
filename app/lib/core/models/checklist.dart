/// CONTRACT §4 Checklist / ChecklistItem.
class ChecklistItem {
  const ChecklistItem({
    required this.id,
    required this.text,
    required this.critical,
    required this.status,
    this.note,
  });

  final String id;
  final String text;
  final bool critical;
  final String status; // ChecklistStatus
  final String? note;

  factory ChecklistItem.fromJson(Map<String, dynamic> j) => ChecklistItem(
        id: j['id'] as String,
        text: j['text'] as String,
        critical: j['critical'] as bool? ?? false,
        status: j['status'] as String? ?? 'pending',
        note: j['note'] as String?,
      );

  ChecklistItem copyWith({String? status, String? note}) => ChecklistItem(
        id: id,
        text: text,
        critical: critical,
        status: status ?? this.status,
        note: note ?? this.note,
      );
}

class ChecklistSection {
  const ChecklistSection({required this.title, required this.items});

  final String title;
  final List<ChecklistItem> items;

  factory ChecklistSection.fromJson(Map<String, dynamic> j) => ChecklistSection(
        title: j['title'] as String,
        items: (j['items'] as List)
            .map((e) => ChecklistItem.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}

class Checklist {
  const Checklist({
    required this.sessionId,
    required this.machineType,
    required this.standardRefs,
    required this.sections,
  });

  final String sessionId;
  final String machineType;
  final List<String> standardRefs;
  final List<ChecklistSection> sections;

  factory Checklist.fromJson(Map<String, dynamic> j) => Checklist(
        sessionId: j['session_id'] as String,
        machineType: j['machine_type'] as String,
        standardRefs:
            (j['standard_refs'] as List).map((e) => e as String).toList(),
        sections: (j['sections'] as List)
            .map((e) => ChecklistSection.fromJson(e as Map<String, dynamic>))
            .toList(),
      );
}
