
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:vesta/features/auth/application/auth_provider.dart';

class LoginScreen extends ConsumerWidget {
  const LoginScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final authState = ref.watch(authProvider);

    return Scaffold(
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text('Vesta', style: Theme.of(context).textTheme.headlineLarge),
              const SizedBox(height: 48),
              TextField(
                controller: ref.read(authProvider.notifier).emailController,
                decoration: const InputDecoration(
                  labelText: 'Email',
                  border: OutlineInputBorder(),
                ),
                keyboardType: TextInputType.emailAddress,
              ),
              const SizedBox(height: 16),
              TextField(
                controller: ref.read(authProvider.notifier).passwordController,
                decoration: InputDecoration(
                  labelText: 'Password',
                  border: const OutlineInputBorder(),
                  errorText: authState.hasError ? 'Invalid credentials' : null,
                ),
                obscureText: true,
              ),
              const SizedBox(height: 24),
              authState.isLoading
                  ? const CircularProgressIndicator()
                  : FilledButton(
                      onPressed: () => ref.read(authProvider.notifier).login(),
                      child: const Text('Login'),
                    ),
            ],
          ),
        ),
      ),
    );
  }
}
