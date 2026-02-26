'''
import 'package:flutter/material.dart';
import 'package:riverpod_annotation/riverpod_annotation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:dio/dio.dart';
import 'package:vesta/core/api_client.dart';

part 'auth_provider.g.dart';

class AuthState {
  final bool isAuthenticated;
  final bool isLoading;
  final bool hasError;

  AuthState({
    this.isAuthenticated = false,
    this.isLoading = false,
    this.hasError = false,
  });

  AuthState copyWith({
    bool? isAuthenticated,
    bool? isLoading,
    bool? hasError,
  }) {
    return AuthState(
      isAuthenticated: isAuthenticated ?? this.isAuthenticated,
      isLoading: isLoading ?? this.isLoading,
      hasError: hasError ?? this.hasError,
    );
  }
}

@riverpod
class Auth extends _$Auth {
  final emailController = TextEditingController();
  final passwordController = TextEditingController();
  final _storage = const FlutterSecureStorage();
  late final DioClient _dioClient;

  @override
  Future<AuthState> build() async {
    _dioClient = DioClient(Dio(), _storage);
    final token = await _storage.read(key: 'auth_token');
    return AuthState(isAuthenticated: token != null);
  }

  Future<void> login() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async {
      try {
        final response = await _dioClient.dio.post(
          '/login/access-token',
          data: FormData.fromMap({
            'username': emailController.text,
            'password': passwordController.text,
          }),
          options: Options(
            contentType: Headers.formUrlEncodedContentType,
          ),
        );

        if (response.statusCode == 200) {
          final token = response.data['access_token'];
          await _storage.write(key: 'auth_token', value: token);
          return AuthState(isAuthenticated: true);
        } else {
          return AuthState(hasError: true);
        }
      } catch (e) {
        return AuthState(hasError: true);
      }
    });
  }

  Future<void> logout() async {
    state = const AsyncValue.loading();
    await _storage.delete(key: 'auth_token');
    state = AsyncValue.data(AuthState(isAuthenticated: false));
  }
}
''