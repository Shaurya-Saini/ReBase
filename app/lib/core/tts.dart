import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_tts/flutter_tts.dart';

/// On-device text-to-speech (A6/A10). Default free/offline playback; the backend
/// Sarvam TTS (E24) is an optional higher-quality upgrade.
class TtsService {
  final FlutterTts _tts = FlutterTts();

  /// [lang] is a CONTRACT Lang, e.g. `hi-IN`.
  Future<void> speak(String text, String lang) async {
    await _tts.setLanguage(lang);
    await _tts.stop();
    await _tts.speak(text);
  }

  Future<void> stop() => _tts.stop();
}

final ttsProvider = Provider<TtsService>((ref) => TtsService());
