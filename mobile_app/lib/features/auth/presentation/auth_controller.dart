import 'package:flutter/foundation.dart';

import '../../../core/storage/token_storage.dart';
import '../data/auth_repository.dart';

class AuthController extends ChangeNotifier {
  AuthRepository? _repo;
  TokenStorage? _tokenStorage;

  bool _isLoading = true;
  bool _isAuthenticated = false;
  String? error;

  bool get isLoading => _isLoading;
  bool get isAuthenticated => _isAuthenticated;

  Future<void> bind({
    required AuthRepository repo,
    required TokenStorage tokenStorage,
  }) async {
    _repo = repo;
    _tokenStorage = tokenStorage;
    await _restoreSession();
  }

  Future<void> _restoreSession() async {
    if (!_isLoading) return;
    final token = await _tokenStorage?.readToken();
    _isAuthenticated = token != null && token.isNotEmpty;
    _isLoading = false;
    notifyListeners();
  }

  Future<bool> login(String email, String password) async {
    error = null;
    notifyListeners();

    try {
      final token = await _repo!.login(email: email, password: password);
      await _tokenStorage!.saveToken(token);
      _isAuthenticated = true;
      notifyListeners();
      return true;
    } catch (e) {
      error = e.toString();
      notifyListeners();
      return false;
    }
  }

  Future<void> logout() async {
    await _tokenStorage?.clear();
    _isAuthenticated = false;
    notifyListeners();
  }
}
