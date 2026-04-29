import 'dart:convert';

class ChatRequest {
  ChatRequest({
    required this.userId,
    required this.message,
    this.wantVoice = true,
    this.sessionId,
  });

  final int userId;
  final String message;
  final bool wantVoice;
  final int? sessionId;

  Map<String, dynamic> toJson() => {
        'user_id': userId,
        'message': message,
        'want_voice': wantVoice,
        'session_id': sessionId,
      };
}

class ChatResponseModel {
  ChatResponseModel({
    required this.response,
    required this.sessionId,
    this.voiceAudioBase64,
  });

  final String response;
  final int sessionId;
  final String? voiceAudioBase64;

  factory ChatResponseModel.fromJson(Map<String, dynamic> json) {
    return ChatResponseModel(
      response: json['response'] as String,
      sessionId: json['session_id'] as int,
      voiceAudioBase64: json['voice_audio'] as String?,
    );
  }

  List<int>? decodeVoiceBytes() {
    final input = voiceAudioBase64;
    if (input == null || input.isEmpty) return null;
    return base64Decode(input);
  }
}
