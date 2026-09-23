import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for English (`en`).
class AppLocalizationsEn extends AppLocalizations {
  AppLocalizationsEn([String locale = 'en']) : super(locale);

  @override
  String get appTitle => 'ReBase';

  @override
  String get action_continue => 'Continue';

  @override
  String get action_start_session => 'Start session';

  @override
  String get action_complete => 'Complete';

  @override
  String get action_start_work => 'Start work';

  @override
  String get action_end_session => 'End session';

  @override
  String get action_ack => 'Acknowledge';

  @override
  String get nav_training => 'Training';

  @override
  String get login_title => 'Sign in';

  @override
  String get login_pin => 'Enter PIN';

  @override
  String get login_pick_operator => 'Select operator';

  @override
  String get login_language => 'Language';

  @override
  String get mode_title => 'Choose mode';

  @override
  String get mode_unmounted => 'Personal time';

  @override
  String get mode_mounted => 'Start shift';

  @override
  String get dashboard_title => 'My day';

  @override
  String get dashboard_hours => 'Hours worked';

  @override
  String get dashboard_rest => 'Rest status';

  @override
  String get rest_ok => 'OK';

  @override
  String get rest_warning => 'Rest soon';

  @override
  String get rest_must => 'Rest required';

  @override
  String get job_title => 'Job';

  @override
  String get job_estimate => 'Estimated time';

  @override
  String get checklist_title => 'Pre-start checklist';

  @override
  String get checklist_complete_blocked => 'Fix critical defects before starting';

  @override
  String get briefing_title => 'Briefing';

  @override
  String get live_title => 'Live session';

  @override
  String get assistant_title => 'Assistant';

  @override
  String get assistant_hint => 'Hold to speak';

  @override
  String get alert_seatbelt_off => 'Seatbelt not fastened';

  @override
  String get alert_drowsiness => 'Operator appears drowsy';

  @override
  String get alert_distraction => 'Operator distracted';

  @override
  String get alert_operator_absent => 'Operator not detected';

  @override
  String get alert_proximity => 'Person or obstacle too close';

  @override
  String get alert_excessive_idle => 'Excessive idling';

  @override
  String get alert_overheat => 'Hydraulic system overheating';

  @override
  String get alert_overload => 'Load over safe limit';

  @override
  String get alert_unsafe_operation => 'Unsafe operation detected';
}
