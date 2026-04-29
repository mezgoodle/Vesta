import 'package:dio/dio.dart';

import '../storage/token_storage.dart';
import 'auth_interceptor.dart';

class ApiClient {
  ApiClient({required String baseUrl, required TokenStorage tokenStorage})
      : dio = Dio(
          BaseOptions(
            baseUrl: baseUrl,
            connectTimeout: const Duration(seconds: 15),
            receiveTimeout: const Duration(seconds: 45),
            headers: {'Accept': 'application/json'},
          ),
        ) {
    dio.interceptors.add(AuthInterceptor(tokenStorage));
  }

  final Dio dio;
}
