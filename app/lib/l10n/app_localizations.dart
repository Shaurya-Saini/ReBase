import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/widgets.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:intl/intl.dart' as intl;

import 'app_localizations_en.dart';
import 'app_localizations_hi.dart';
import 'app_localizations_ta.dart';

// ignore_for_file: type=lint

/// Callers can lookup localized strings with an instance of AppLocalizations
/// returned by `AppLocalizations.of(context)`.
///
/// Applications need to include `AppLocalizations.delegate()` in their app's
/// `localizationDelegates` list, and the locales they support in the app's
/// `supportedLocales` list. For example:
///
/// ```dart
/// import 'l10n/app_localizations.dart';
///
/// return MaterialApp(
///   localizationsDelegates: AppLocalizations.localizationsDelegates,
///   supportedLocales: AppLocalizations.supportedLocales,
///   home: MyApplicationHome(),
/// );
/// ```
///
/// ## Update pubspec.yaml
///
/// Please make sure to update your pubspec.yaml to include the following
/// packages:
///
/// ```yaml
/// dependencies:
///   # Internationalization support.
///   flutter_localizations:
///     sdk: flutter
///   intl: any # Use the pinned version from flutter_localizations
///
///   # Rest of dependencies
/// ```
///
/// ## iOS Applications
///
/// iOS applications define key application metadata, including supported
/// locales, in an Info.plist file that is built into the application bundle.
/// To configure the locales supported by your app, you’ll need to edit this
/// file.
///
/// First, open your project’s ios/Runner.xcworkspace Xcode workspace file.
/// Then, in the Project Navigator, open the Info.plist file under the Runner
/// project’s Runner folder.
///
/// Next, select the Information Property List item, select Add Item from the
/// Editor menu, then select Localizations from the pop-up menu.
///
/// Select and expand the newly-created Localizations item then, for each
/// locale your application supports, add a new item and select the locale
/// you wish to add from the pop-up menu in the Value field. This list should
/// be consistent with the languages listed in the AppLocalizations.supportedLocales
/// property.
abstract class AppLocalizations {
  AppLocalizations(String locale)
      : localeName = intl.Intl.canonicalizedLocale(locale.toString());

  final String localeName;

  static AppLocalizations? of(BuildContext context) {
    return Localizations.of<AppLocalizations>(context, AppLocalizations);
  }

  static const LocalizationsDelegate<AppLocalizations> delegate =
      _AppLocalizationsDelegate();

  /// A list of this localizations delegate along with the default localizations
  /// delegates.
  ///
  /// Returns a list of localizations delegates containing this delegate along with
  /// GlobalMaterialLocalizations.delegate, GlobalCupertinoLocalizations.delegate,
  /// and GlobalWidgetsLocalizations.delegate.
  ///
  /// Additional delegates can be added by appending to this list in
  /// MaterialApp. This list does not have to be used at all if a custom list
  /// of delegates is preferred or required.
  static const List<LocalizationsDelegate<dynamic>> localizationsDelegates =
      <LocalizationsDelegate<dynamic>>[
    delegate,
    GlobalMaterialLocalizations.delegate,
    GlobalCupertinoLocalizations.delegate,
    GlobalWidgetsLocalizations.delegate,
  ];

  /// A list of this localizations delegate's supported locales.
  static const List<Locale> supportedLocales = <Locale>[
    Locale('en'),
    Locale('hi'),
    Locale('ta')
  ];

  /// No description provided for @appTitle.
  ///
  /// In en, this message translates to:
  /// **'ReBase'**
  String get appTitle;

  /// No description provided for @action_continue.
  ///
  /// In en, this message translates to:
  /// **'Continue'**
  String get action_continue;

  /// No description provided for @action_start_session.
  ///
  /// In en, this message translates to:
  /// **'Start session'**
  String get action_start_session;

  /// No description provided for @action_complete.
  ///
  /// In en, this message translates to:
  /// **'Complete'**
  String get action_complete;

  /// No description provided for @action_start_work.
  ///
  /// In en, this message translates to:
  /// **'Start work'**
  String get action_start_work;

  /// No description provided for @action_end_session.
  ///
  /// In en, this message translates to:
  /// **'End session'**
  String get action_end_session;

  /// No description provided for @action_ack.
  ///
  /// In en, this message translates to:
  /// **'Acknowledge'**
  String get action_ack;

  /// No description provided for @nav_training.
  ///
  /// In en, this message translates to:
  /// **'Training'**
  String get nav_training;

  /// No description provided for @login_title.
  ///
  /// In en, this message translates to:
  /// **'Sign in'**
  String get login_title;

  /// No description provided for @login_pin.
  ///
  /// In en, this message translates to:
  /// **'Enter PIN'**
  String get login_pin;

  /// No description provided for @login_pick_operator.
  ///
  /// In en, this message translates to:
  /// **'Select operator'**
  String get login_pick_operator;

  /// No description provided for @login_language.
  ///
  /// In en, this message translates to:
  /// **'Language'**
  String get login_language;

  /// No description provided for @mode_title.
  ///
  /// In en, this message translates to:
  /// **'Choose mode'**
  String get mode_title;

  /// No description provided for @mode_unmounted.
  ///
  /// In en, this message translates to:
  /// **'Personal time'**
  String get mode_unmounted;

  /// No description provided for @mode_mounted.
  ///
  /// In en, this message translates to:
  /// **'Start shift'**
  String get mode_mounted;

  /// No description provided for @dashboard_title.
  ///
  /// In en, this message translates to:
  /// **'My day'**
  String get dashboard_title;

  /// No description provided for @dashboard_hours.
  ///
  /// In en, this message translates to:
  /// **'Hours worked'**
  String get dashboard_hours;

  /// No description provided for @dashboard_rest.
  ///
  /// In en, this message translates to:
  /// **'Rest status'**
  String get dashboard_rest;

  /// No description provided for @rest_ok.
  ///
  /// In en, this message translates to:
  /// **'OK'**
  String get rest_ok;

  /// No description provided for @rest_warning.
  ///
  /// In en, this message translates to:
  /// **'Rest soon'**
  String get rest_warning;

  /// No description provided for @rest_must.
  ///
  /// In en, this message translates to:
  /// **'Rest required'**
  String get rest_must;

  /// No description provided for @job_title.
  ///
  /// In en, this message translates to:
  /// **'Job'**
  String get job_title;

  /// No description provided for @job_estimate.
  ///
  /// In en, this message translates to:
  /// **'Estimated time'**
  String get job_estimate;

  /// No description provided for @checklist_title.
  ///
  /// In en, this message translates to:
  /// **'Pre-start checklist'**
  String get checklist_title;

  /// No description provided for @checklist_complete_blocked.
  ///
  /// In en, this message translates to:
  /// **'Fix critical defects before starting'**
  String get checklist_complete_blocked;

  /// No description provided for @briefing_title.
  ///
  /// In en, this message translates to:
  /// **'Briefing'**
  String get briefing_title;

  /// No description provided for @live_title.
  ///
  /// In en, this message translates to:
  /// **'Live session'**
  String get live_title;

  /// No description provided for @assistant_title.
  ///
  /// In en, this message translates to:
  /// **'Assistant'**
  String get assistant_title;

  /// No description provided for @assistant_hint.
  ///
  /// In en, this message translates to:
  /// **'Hold to speak'**
  String get assistant_hint;

  /// Alert shown by type; backend message stays English for logs
  ///
  /// In en, this message translates to:
  /// **'Seatbelt not fastened'**
  String get alert_seatbelt_off;

  /// No description provided for @alert_drowsiness.
  ///
  /// In en, this message translates to:
  /// **'Operator appears drowsy'**
  String get alert_drowsiness;

  /// No description provided for @alert_distraction.
  ///
  /// In en, this message translates to:
  /// **'Operator distracted'**
  String get alert_distraction;

  /// No description provided for @alert_operator_absent.
  ///
  /// In en, this message translates to:
  /// **'Operator not detected'**
  String get alert_operator_absent;

  /// No description provided for @alert_proximity.
  ///
  /// In en, this message translates to:
  /// **'Person or obstacle too close'**
  String get alert_proximity;

  /// No description provided for @alert_excessive_idle.
  ///
  /// In en, this message translates to:
  /// **'Excessive idling'**
  String get alert_excessive_idle;

  /// No description provided for @alert_overheat.
  ///
  /// In en, this message translates to:
  /// **'Hydraulic system overheating'**
  String get alert_overheat;

  /// No description provided for @alert_overload.
  ///
  /// In en, this message translates to:
  /// **'Load over safe limit'**
  String get alert_overload;

  /// No description provided for @alert_unsafe_operation.
  ///
  /// In en, this message translates to:
  /// **'Unsafe operation detected'**
  String get alert_unsafe_operation;
}

class _AppLocalizationsDelegate
    extends LocalizationsDelegate<AppLocalizations> {
  const _AppLocalizationsDelegate();

  @override
  Future<AppLocalizations> load(Locale locale) {
    return SynchronousFuture<AppLocalizations>(lookupAppLocalizations(locale));
  }

  @override
  bool isSupported(Locale locale) =>
      <String>['en', 'hi', 'ta'].contains(locale.languageCode);

  @override
  bool shouldReload(_AppLocalizationsDelegate old) => false;
}

AppLocalizations lookupAppLocalizations(Locale locale) {
  // Lookup logic when only language code is specified.
  switch (locale.languageCode) {
    case 'en':
      return AppLocalizationsEn();
    case 'hi':
      return AppLocalizationsHi();
    case 'ta':
      return AppLocalizationsTa();
  }

  throw FlutterError(
      'AppLocalizations.delegate failed to load unsupported locale "$locale". This is likely '
      'an issue with the localizations generation tool. Please file an issue '
      'on GitHub with a reproducible sample app and the gen-l10n configuration '
      'that was used.');
}
