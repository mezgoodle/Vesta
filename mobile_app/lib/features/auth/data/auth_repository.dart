import 'package:dio/dio.dart';

import '../../../core/network/api_client.dart';

class AuthRepository {
  AuthRepository(this._client);

  final ApiClient _client;

  Future<String> login({required String email, required String password}) async {
    final response = await _client.dio.post<Map<String, dynamic>>(
      '/api/v1/login/access-token',
      data: {'username': email, 'password': password},
      options: Options(contentType: Headers.formUrlEncodedContentType),
    );

    final token = response.data?['access_token'] as String?;
    if (token == null || token.isEmpty) {
      throw Exception('No access_token in response');
    }
    return token;
  }
}
