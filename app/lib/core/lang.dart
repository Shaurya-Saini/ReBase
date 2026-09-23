/// Map the app locale code (en/hi/ta) to the CONTRACT `Lang` (en-IN/hi-IN/ta-IN).
String contractLang(String languageCode) => switch (languageCode) {
      'hi' => 'hi-IN',
      'ta' => 'ta-IN',
      'te' => 'te-IN',
      _ => 'en-IN',
    };

/// Map the app locale code to a `speech_to_text` locale id (e.g. hi_IN).
String sttLocaleId(String languageCode) => switch (languageCode) {
      'hi' => 'hi_IN',
      'ta' => 'ta_IN',
      'te' => 'te_IN',
      _ => 'en_IN',
    };
