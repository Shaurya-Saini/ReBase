import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:speech_to_text/speech_to_text.dart';

/// On-device speech-to-text (A10). Push-to-talk; no audio leaves the device.
class SttService {
  final SpeechToText _stt = SpeechToText();

  Future<bool> init() => _stt.initialize();

  Future<void> listen({
    required String localeId,
    required void Function(String text) onResult,
  }) =>
      _stt.listen(
        onResult: (r) => onResult(r.recognizedWords),
        listenOptions: SpeechListenOptions(localeId: localeId),
      );

  Future<void> stop() => _stt.stop();

  bool get isListening => _stt.isListening;
}

final sttProvider = Provider<SttService>((ref) => SttService());
