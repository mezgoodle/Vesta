import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'device_controller.dart';

class HomeControlScreen extends StatefulWidget {
  const HomeControlScreen({super.key});

  @override
  State<HomeControlScreen> createState() => _HomeControlScreenState();
}

class _HomeControlScreenState extends State<HomeControlScreen> {
  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      context.read<DeviceController>().loadDevices();
    });
  }

  @override
  Widget build(BuildContext context) {
    final devices = context.watch<DeviceController>();

    return Scaffold(
      appBar: AppBar(title: const Text('Home Control')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showCreateDialog(context),
        icon: const Icon(Icons.add),
        label: const Text('Add device'),
      ),
      body: devices.loading
          ? const Center(child: CircularProgressIndicator())
          : RefreshIndicator(
              onRefresh: devices.loadDevices,
              child: ListView(
                padding: const EdgeInsets.all(12),
                children: [
                  if (devices.error != null)
                    Text(
                      devices.error!,
                      style: const TextStyle(color: Colors.redAccent),
                    ),
                  ...devices.devices.map(
                    (device) => Card(
                      child: ListTile(
                        title: Text(device.name),
                        subtitle: Text(
                          '${device.entityId} • ${device.room ?? 'Unknown room'}',
                        ),
                        trailing: Wrap(
                          spacing: 8,
                          children: [
                            IconButton(
                              icon: const Icon(Icons.edit),
                              onPressed: () => devices.toggleRename(device),
                            ),
                            IconButton(
                              icon: const Icon(Icons.delete),
                              onPressed: () => devices.delete(device.id),
                            ),
                          ],
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
    );
  }

  Future<void> _showCreateDialog(BuildContext context) async {
    final nameCtrl = TextEditingController();
    final entityCtrl = TextEditingController();
    final roomCtrl = TextEditingController();

    await showDialog<void>(
      context: context,
      builder: (_) {
        return AlertDialog(
          title: const Text('Create device'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextField(
                controller: nameCtrl,
                decoration: const InputDecoration(labelText: 'Name'),
              ),
              TextField(
                controller: entityCtrl,
                decoration: const InputDecoration(labelText: 'Entity ID'),
              ),
              TextField(
                controller: roomCtrl,
                decoration: const InputDecoration(labelText: 'Room'),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () async {
                await context.read<DeviceController>().createDevice(
                      name: nameCtrl.text,
                      entityId: entityCtrl.text,
                      room: roomCtrl.text.isEmpty ? null : roomCtrl.text,
                    );
                if (context.mounted) Navigator.pop(context);
              },
              child: const Text('Create'),
            ),
          ],
        );
      },
    );
  }
}
