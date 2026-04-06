import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'core/config/app_config.dart';
import 'core/network/api_client.dart';
import 'core/storage/token_storage.dart';
import 'features/auth/data/auth_repository.dart';
import 'features/auth/presentation/auth_controller.dart';
import 'features/auth/presentation/login_screen.dart';
import 'features/chat/data/chat_repository.dart';
import 'features/chat/presentation/chat_controller.dart';
import 'features/chat/presentation/chat_screen.dart';
import 'features/devices/data/device_repository.dart';
import 'features/devices/presentation/device_controller.dart';
import 'features/devices/presentation/home_control_screen.dart';
import 'features/voice/data/audio_player_service.dart';
import 'features/voice/data/speech_service.dart';

class VestaApp extends StatelessWidget {
  const VestaApp({super.key});

  @override
  Widget build(BuildContext context) {
    final tokenStorage = TokenStorage();
    final apiClient = ApiClient(
      baseUrl: AppConfig.apiBaseUrl,
      tokenStorage: tokenStorage,
    );

    return MultiProvider(
      providers: [
        Provider<TokenStorage>.value(value: tokenStorage),
        Provider<ApiClient>.value(value: apiClient),
        ProxyProvider<ApiClient, AuthRepository>(
          update: (_, client, __) => AuthRepository(client),
        ),
        ProxyProvider<ApiClient, ChatRepository>(
          update: (_, client, __) => ChatRepository(client),
        ),
        ProxyProvider<ApiClient, DeviceRepository>(
          update: (_, client, __) => DeviceRepository(client),
        ),
        Provider<SpeechService>(create: (_) => SpeechService()),
        Provider<AudioPlayerService>(create: (_) => AudioPlayerService()),
        ChangeNotifierProxyProvider2<AuthRepository, TokenStorage, AuthController>(
          create: (_) => AuthController(),
          update: (_, repo, storage, controller) =>
              controller!..bind(repo: repo, tokenStorage: storage),
        ),
        ChangeNotifierProxyProvider3<ChatRepository, SpeechService,
            AudioPlayerService, ChatController>(
          create: (_) => ChatController(),
          update: (_, repo, speech, audio, controller) =>
              controller!..bind(repo: repo, speechService: speech, audioService: audio),
        ),
        ChangeNotifierProxyProvider<DeviceRepository, DeviceController>(
          create: (_) => DeviceController(),
          update: (_, repo, controller) => controller!..bind(repo),
        ),
      ],
      child: MaterialApp(
        title: 'Vesta Mobile',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          brightness: Brightness.dark,
          scaffoldBackgroundColor: const Color(0xFF070B14),
          colorScheme: const ColorScheme.dark(
            primary: Color(0xFF5DE2FF),
            secondary: Color(0xFF00B7FF),
          ),
        ),
        home: Consumer<AuthController>(
          builder: (_, auth, __) {
            if (auth.isLoading) {
              return const Scaffold(
                body: Center(child: CircularProgressIndicator()),
              );
            }
            return auth.isAuthenticated ? const _RootTabs() : const LoginScreen();
          },
        ),
      ),
    );
  }
}

class _RootTabs extends StatefulWidget {
  const _RootTabs();

  @override
  State<_RootTabs> createState() => _RootTabsState();
}

class _RootTabsState extends State<_RootTabs> {
  int index = 0;

  final screens = const [
    ChatScreen(),
    HomeControlScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: screens[index],
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: index,
        onTap: (value) => setState(() => index = value),
        items: const [
          BottomNavigationBarItem(icon: Icon(Icons.smart_toy), label: 'JARVIS'),
          BottomNavigationBarItem(icon: Icon(Icons.home), label: 'Home Control'),
        ],
      ),
    );
  }
}
