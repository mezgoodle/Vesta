import 'dart:math' as math;

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../auth/presentation/auth_controller.dart';
import '../../voice/presentation/voice_status_badge.dart';
import 'chat_controller.dart';

class ChatScreen extends StatefulWidget {
  const ChatScreen({super.key});

  @override
  State<ChatScreen> createState() => _ChatScreenState();
}

class _ChatScreenState extends State<ChatScreen> {
  final controller = TextEditingController();

  @override
  Widget build(BuildContext context) {
    final chat = context.watch<ChatController>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('JARVIS'),
        actions: [
          IconButton(
            onPressed: () => context.read<AuthController>().logout(),
            icon: const Icon(Icons.logout),
          ),
        ],
      ),
      body: Column(
        children: [
          const SizedBox(height: 16),
          _JarvisCore(status: chat.statusText, state: chat.state),
          if (chat.draftSpeech.isNotEmpty)
            Padding(
              padding: const EdgeInsets.all(12),
              child: Text('"${chat.draftSpeech}"'),
            ),
          Expanded(
            child: ListView.builder(
              padding: const EdgeInsets.all(12),
              itemCount: chat.messages.length,
              itemBuilder: (_, index) {
                final item = chat.messages[index];
                final isUser = item.role == 'user';
                return Align(
                  alignment:
                      isUser ? Alignment.centerRight : Alignment.centerLeft,
                  child: Card(
                    color: isUser
                        ? const Color(0xFF123E52)
                        : const Color(0xFF1A1F2B),
                    child: Padding(
                      padding: const EdgeInsets.all(10),
                      child: Text(item.text),
                    ),
                  ),
                );
              },
            ),
          ),
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: controller,
                    decoration: const InputDecoration(hintText: 'Type a message'),
                  ),
                ),
                const SizedBox(width: 8),
                IconButton(
                  onPressed: () async {
                    final text = controller.text;
                    controller.clear();
                    await chat.sendText(text);
                  },
                  icon: const Icon(Icons.send),
                ),
              ],
            ),
          ),
        ],
      ),
      floatingActionButton: _VoiceActions(chat: chat),
    );
  }
}

class _VoiceActions extends StatelessWidget {
  const _VoiceActions({required this.chat});

  final ChatController chat;

  @override
  Widget build(BuildContext context) {
    return Column(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        FloatingActionButton.extended(
          heroTag: 'tap_to_talk',
          onPressed: () => chat.startListening(),
          icon: const Icon(Icons.mic),
          label: const Text('Tap to talk'),
        ),
        const SizedBox(height: 8),
        GestureDetector(
          onLongPressStart: (_) => chat.startListening(),
          onLongPressEnd: (_) => chat.stopListening(),
          child: FloatingActionButton.extended(
            heroTag: 'hold_to_talk',
            onPressed: () {},
            icon: const Icon(Icons.hearing),
            label: const Text('Hold to talk'),
          ),
        ),
      ],
    );
  }
}

class _JarvisCore extends StatefulWidget {
  const _JarvisCore({required this.status, required this.state});

  final String status;
  final JarvisState state;

  @override
  State<_JarvisCore> createState() => _JarvisCoreState();
}

class _JarvisCoreState extends State<_JarvisCore>
    with SingleTickerProviderStateMixin {
  late final AnimationController animation;

  @override
  void initState() {
    super.initState();
    animation = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);
  }

  @override
  void dispose() {
    animation.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final glowMultiplier = switch (widget.state) {
      JarvisState.listening => 1.5,
      JarvisState.thinking => 1.2,
      JarvisState.speaking => 1.8,
      JarvisState.idle => 1.0,
    };

    return Column(
      children: [
        AnimatedBuilder(
          animation: animation,
          builder: (_, __) {
            final scale = 48 + (math.sin(animation.value * math.pi) * 16);
            return Container(
              width: scale,
              height: scale,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: const Color(0xFF52E8FF),
                boxShadow: [
                  BoxShadow(
                    color: const Color(0xFF52E8FF)
                        .withOpacity(0.55 * glowMultiplier),
                    blurRadius: 40 * glowMultiplier,
                    spreadRadius: 6 * glowMultiplier,
                  ),
                ],
              ),
            );
          },
        ),
        const SizedBox(height: 10),
        VoiceStatusBadge(label: widget.status),
      ],
    );
  }
}
