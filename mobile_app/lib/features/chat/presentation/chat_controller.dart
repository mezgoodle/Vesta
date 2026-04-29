import 'package:flutter/foundation.dart';

import '../../voice/data/audio_player_service.dart';
import '../../voice/data/speech_service.dart';
import '../data/chat_models.dart';
import '../data/chat_repository.dart';

enum JarvisState { idle, listening, thinking, speaking }

class ChatMessage {
  ChatMessage(this.role, this.text);

  final String role;
  final String text;
}

class ChatController extends ChangeNotifier {
  static const int demoUserId = 1;

  ChatRepository? _repo;
  SpeechService? _speechService;
  AudioPlayerService? _audioService;

  final List<ChatMessage> messages = [];

  JarvisState state = JarvisState.idle;
  String draftSpeech = '';
  int? sessionId;

  void bind({
    required ChatRepository repo,
    required SpeechService speechService,
    required AudioPlayerService audioService,
  }) {
    _repo = repo;
    _speechService = speechService;
    _audioService = audioService;
  }

  String get statusText {
    switch (state) {
      case JarvisState.listening:
        return 'Listening';
      case JarvisState.thinking:
        return 'Thinking';
      case JarvisState.speaking:
        return 'Speaking';
      case JarvisState.idle:
        return 'Ready';
    }
  }

  Future<void> sendText(String text) async {
    if (text.trim().isEmpty) return;
    messages.add(ChatMessage('user', text));
    state = JarvisState.thinking;
    notifyListeners();

    final response = await _repo!.process(
      ChatRequest(
        userId: demoUserId,
        message: text,
        wantVoice: true,
        sessionId: sessionId,
      ),
    );

    sessionId = response.sessionId;
    messages.add(ChatMessage('assistant', response.response));

    state = JarvisState.speaking;
    notifyListeners();

    final decodedVoice = response.decodeVoiceBytes();
    if (decodedVoice != null && decodedVoice.isNotEmpty) {
      await _audioService!.playBytes(decodedVoice);
    } else {
      final fallback = await _repo!.synthesizeFallback(response.response);
      await _audioService!.playBytes(fallback);
    }

    state = JarvisState.idle;
    notifyListeners();
  }

  Future<void> startListening() async {
    final isReady = await _speechService!.initialize();
    if (!isReady) return;

    state = JarvisState.listening;
    draftSpeech = '';
    notifyListeners();

    await _speechService!.start(
      onResult: (text, isFinal) async {
        draftSpeech = text;
        notifyListeners();

        if (isFinal && text.trim().isNotEmpty) {
          await _speechService!.stop();
          await sendText(text);
        }
      },
    );
  }

  Future<void> stopListening() async {
    await _speechService?.stop();
    if (state == JarvisState.listening) {
      state = JarvisState.idle;
      notifyListeners();
    }
  }
}
