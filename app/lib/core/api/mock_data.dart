import 'package:app/core/models/models.dart';

/// In-memory fixtures matching CONTRACT §4 examples — power the whole app with
/// `USE_MOCK=true` (no backend).
class MockData {
  static Operator operator1() => const Operator(
        id: 'op_001',
        name: 'Ravi Kumar',
        lang: 'ta-IN',
        experience: {'excavator': 'expert', 'wheel_loader': 'novice'},
        hoursToday: 3.5,
        hours7d: 41.0,
        rest: RestInfo(status: 'ok'),
      );

  static Operator operator2() => const Operator(
        id: 'op_002',
        name: 'Amit Singh',
        lang: 'hi-IN',
        experience: {'dump_truck': 'intermediate'},
        hoursToday: 1.0,
        hours7d: 20.0,
        rest: RestInfo(status: 'ok'),
      );

  static List<Operator> operators() => [operator1(), operator2()];

  static Machine machine1() => const Machine(
        id: 'mc_001',
        type: 'excavator',
        model: 'Generic 20t Excavator',
        serial: 'EX20-0001',
        hourMeter: 4521.3,
        status: 'available',
        lastInspection: '2026-09-23T02:10:00Z',
      );

  static Machine machine2() => const Machine(
        id: 'mc_002',
        type: 'wheel_loader',
        model: 'Generic Wheel Loader',
        serial: 'WL-0002',
        hourMeter: 1200.0,
        status: 'available',
      );

  static List<Machine> machines() => [machine1(), machine2()];

  static Job job1() => const Job(
        id: 'job_001',
        projectId: 'prj_001',
        title: 'Trench excavation – Block C',
        site: 'Site 2, North Pit',
        machineType: 'excavator',
        scheduledStart: '2026-09-24T03:30:00Z',
        plannedHours: 6.0,
        status: 'scheduled',
      );

  static Assignment assignment1() => Assignment(
        id: 'asg_001',
        operatorId: 'op_001',
        date: '2026-09-24',
        shift: 'day',
        job: job1(),
        machine: machine1(),
      );

  static Estimate estimate1() => const Estimate(
        jobId: 'job_001',
        estimatedHours: 6.8,
        rangeHours: [5.9, 7.6],
        factors: [
          EstimateFactor(
              name: 'weather', effectPct: 8, note: 'Light rain forecast'),
          EstimateFactor(
              name: 'operator_experience',
              effectPct: -5,
              note: 'Expert on excavator'),
        ],
        projectCompletionDate: '2026-10-18',
      );

  static Session session1({String state = 'pre_start'}) => Session(
        id: 'ses_001',
        operatorId: 'op_001',
        machineId: 'mc_001',
        jobId: 'job_001',
        state: state,
      );

  static Checklist checklist1(String sessionId) => Checklist(
        sessionId: sessionId,
        machineType: 'excavator',
        standardRefs: const ['MSHA 30 CFR 56.14100', 'ISO 20474'],
        sections: const [
          ChecklistSection(title: 'Walk-around', items: [
            ChecklistItem(
                id: 'chk_01',
                text: 'Check tracks and undercarriage for damage',
                critical: false,
                status: 'pending'),
            ChecklistItem(
                id: 'chk_02',
                text: 'Check hydraulic hoses for leaks',
                critical: true,
                status: 'pending'),
          ]),
        ],
      );

  static Briefing briefing1(String sessionId, String lang) => Briefing(
        sessionId: sessionId,
        lang: lang,
        machineSummary: '20t excavator, 4521 hours, last inspection today.',
        jobSummary: 'Dig 40 m trench, 1.5 m deep, Block C.',
        estimatedHours: 6.8,
        hazards: const [
          'Overhead power line near east edge',
          'Soft ground after rain'
        ],
        reminders: const ['Keep 10 m distance from ground crew'],
      );

  static SessionSummary summary1(String sessionId) => SessionSummary(
        sessionId: sessionId,
        durationHours: 5.9,
        alertsTotal: 4,
        alertsCritical: 1,
        idleMinutes: 22,
      );

  static TrainingModule training1(String machineType, String level) =>
      TrainingModule(
        id: 'trn_ex_novice_01',
        machineType: machineType,
        level: level,
        title: 'Excavator basics before your shift',
        durationMin: 30,
        steps: const [
          TrainingStep(
              kind: 'text',
              content: 'The joystick pattern on this machine is ISO.'),
          TrainingStep(
              kind: 'video',
              content: 'Walk-around inspection',
              url: 'https://example.com/video'),
          TrainingStep(
              kind: 'tip', content: 'Never swing over the ground crew.'),
        ],
        quiz: const [
          QuizQuestion(
            q: 'What must you do if a hydraulic hose leaks?',
            options: ['Ignore it', 'Report and do not start', 'Start slowly'],
            answerIndex: 1,
          ),
        ],
      );

  static AssistantAnswer answer1(String lang) => AssistantAnswer(
        answer:
            'Switch to power mode using the mode button on the right console.',
        lang: lang,
        sources: const [
          AnswerSource(
              doc: 'excavator_manual.md', section: '4.2 Operating modes')
        ],
      );
}
