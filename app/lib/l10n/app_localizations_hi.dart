import 'app_localizations.dart';

// ignore_for_file: type=lint

/// The translations for Hindi (`hi`).
class AppLocalizationsHi extends AppLocalizations {
  AppLocalizationsHi([String locale = 'hi']) : super(locale);

  @override
  String get appTitle => 'ReBase';

  @override
  String get action_continue => 'जारी रखें';

  @override
  String get action_start_session => 'सत्र शुरू करें';

  @override
  String get action_complete => 'पूर्ण करें';

  @override
  String get action_start_work => 'काम शुरू करें';

  @override
  String get action_end_session => 'सत्र समाप्त करें';

  @override
  String get action_ack => 'स्वीकार करें';

  @override
  String get nav_training => 'प्रशिक्षण';

  @override
  String get login_title => 'साइन इन करें';

  @override
  String get login_pin => 'पिन दर्ज करें';

  @override
  String get login_pick_operator => 'ऑपरेटर चुनें';

  @override
  String get login_language => 'भाषा';

  @override
  String get mode_title => 'मोड चुनें';

  @override
  String get mode_unmounted => 'व्यक्तिगत समय';

  @override
  String get mode_mounted => 'शिफ्ट शुरू करें';

  @override
  String get dashboard_title => 'मेरा दिन';

  @override
  String get dashboard_hours => 'काम के घंटे';

  @override
  String get dashboard_rest => 'विश्राम स्थिति';

  @override
  String get rest_ok => 'ठीक है';

  @override
  String get rest_warning => 'जल्द विश्राम करें';

  @override
  String get rest_must => 'विश्राम आवश्यक';

  @override
  String get job_title => 'कार्य';

  @override
  String get job_estimate => 'अनुमानित समय';

  @override
  String get checklist_title => 'प्रारंभ-पूर्व जाँच सूची';

  @override
  String get checklist_complete_blocked => 'शुरू करने से पहले गंभीर खराबी ठीक करें';

  @override
  String get briefing_title => 'ब्रीफिंग';

  @override
  String get live_title => 'लाइव सत्र';

  @override
  String get assistant_title => 'सहायक';

  @override
  String get assistant_hint => 'बोलने के लिए दबाए रखें';

  @override
  String get alert_seatbelt_off => 'सीट बेल्ट नहीं बंधी है';

  @override
  String get alert_drowsiness => 'ऑपरेटर को नींद आ रही है';

  @override
  String get alert_distraction => 'ऑपरेटर का ध्यान भटका है';

  @override
  String get alert_operator_absent => 'ऑपरेटर नहीं मिला';

  @override
  String get alert_proximity => 'व्यक्ति या बाधा बहुत पास है';

  @override
  String get alert_excessive_idle => 'अत्यधिक निष्क्रियता';

  @override
  String get alert_overheat => 'हाइड्रोलिक प्रणाली अधिक गरम';

  @override
  String get alert_overload => 'भार सुरक्षित सीमा से अधिक';

  @override
  String get alert_unsafe_operation => 'असुरक्षित संचालन पाया गया';
}
