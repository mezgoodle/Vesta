import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';
import 'chat_models.dart';

class ChatRepository {
  ChatRepository(this._client);

  final ApiClient _client;

  Future<ChatResponseModel> process(ChatRequest request) async {
    final response = await _client.dio.post<Map<String, dynamic>>(
      '/api/v1/chat/process',
      data: request.toJson(),
    );
    return ChatResponseModel.fromJson(response.data!);
  }

  Future<List<int>> synthesizeFallback(String text) async {
    final response = await _client.dio.post<List<int>>(
      '/api/v1/tts/synthesize',
      data: {'text': text},
      options: Options(responseType: ResponseType.bytes),
    );
    return response.data ?? <int>[];
  }
}
