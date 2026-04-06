import 'dart:typed_data';

import 'package:audioplayers/audioplayers.dart';

class AudioPlayerService {
  final AudioPlayer _player = AudioPlayer();

  Future<void> playBytes(List<int> bytes) async {
    if (bytes.isEmpty) return;
    await _player.play(BytesSource(Uint8List.fromList(bytes)));
  }
}
