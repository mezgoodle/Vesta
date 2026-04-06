class SmartDevice {
  SmartDevice({
    required this.id,
    required this.name,
    required this.entityId,
    this.deviceType,
    this.room,
    required this.userId,
  });

  final int id;
  final String name;
  final String entityId;
  final String? deviceType;
  final String? room;
  final int userId;

  factory SmartDevice.fromJson(Map<String, dynamic> json) => SmartDevice(
        id: json['id'] as int,
        name: json['name'] as String,
        entityId: json['entity_id'] as String,
        deviceType: json['device_type'] as String?,
        room: json['room'] as String?,
        userId: json['user_id'] as int,
      );

  Map<String, dynamic> toCreateJson() => {
        'name': name,
        'entity_id': entityId,
        'device_type': deviceType,
        'room': room,
        'user_id': userId,
      };

  Map<String, dynamic> toUpdateJson() => {
        'name': name,
        'entity_id': entityId,
        'device_type': deviceType,
        'room': room,
      };
}
