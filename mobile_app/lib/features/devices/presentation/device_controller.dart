import 'package:flutter/foundation.dart';

import '../data/device_model.dart';
import '../data/device_repository.dart';

class DeviceController extends ChangeNotifier {
  static const int demoUserId = 1;

  DeviceRepository? _repository;

  bool loading = false;
  String? error;
  List<SmartDevice> devices = [];

  void bind(DeviceRepository repository) {
    _repository = repository;
  }

  Future<void> loadDevices() async {
    loading = true;
    error = null;
    notifyListeners();

    try {
      devices = await _repository!.getDevices(userId: demoUserId);
    } catch (e) {
      error = e.toString();
    } finally {
      loading = false;
      notifyListeners();
    }
  }

  Future<void> createDevice({
    required String name,
    required String entityId,
    String? room,
    String? type,
  }) async {
    final newDevice = SmartDevice(
      id: 0,
      name: name,
      entityId: entityId,
      room: room,
      deviceType: type,
      userId: demoUserId,
    );
    await _repository!.createDevice(newDevice);
    await loadDevices();
  }

  Future<void> toggleRename(SmartDevice device) async {
    final updated = SmartDevice(
      id: device.id,
      name: '${device.name} •',
      entityId: device.entityId,
      room: device.room,
      deviceType: device.deviceType,
      userId: device.userId,
    );
    await _repository!.updateDevice(updated);
    await loadDevices();
  }

  Future<void> delete(int id) async {
    await _repository!.deleteDevice(id);
    await loadDevices();
  }
}
