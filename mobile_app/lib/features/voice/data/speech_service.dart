import 'package:speech_to_text/speech_to_text.dart';

class SpeechService {
  final SpeechToText _speechToText = SpeechToText();

  Future<bool> initialize() => _speechToText.initialize();

  Future<void> start({
    required void Function(String text, bool isFinal) onResult,
  }) async {
    await _speechToText.listen(
      onResult: (result) {
        onResult(result.recognizedWords, result.finalResult);
      },
      listenMode: ListenMode.confirmation,
    );
  }

  Future<void> stop() => _speechToText.stop();
}
