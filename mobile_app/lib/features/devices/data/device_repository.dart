import '../../../core/network/api_client.dart';
import 'device_model.dart';

class DeviceRepository {
  DeviceRepository(this._client);

  final ApiClient _client;

  Future<List<SmartDevice>> getDevices({required int userId}) async {
    final response = await _client.dio.get<List<dynamic>>(
      '/api/v1/devices/',
      queryParameters: {'user_id': userId},
    );

    final list = response.data ?? [];
    return list
        .map((item) => SmartDevice.fromJson(item as Map<String, dynamic>))
        .toList();
  }

  Future<SmartDevice> createDevice(SmartDevice device) async {
    final response = await _client.dio.post<Map<String, dynamic>>(
      '/api/v1/devices/',
      data: device.toCreateJson(),
    );
    return SmartDevice.fromJson(response.data!);
  }

  Future<SmartDevice> updateDevice(SmartDevice device) async {
    final response = await _client.dio.put<Map<String, dynamic>>(
      '/api/v1/devices/${device.id}',
      data: device.toUpdateJson(),
    );
    return SmartDevice.fromJson(response.data!);
  }

  Future<void> deleteDevice(int deviceId) async {
    await _client.dio.delete('/api/v1/devices/$deviceId');
  }
}
