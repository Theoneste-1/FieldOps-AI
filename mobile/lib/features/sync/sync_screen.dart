import 'package:fieldops_ai/core/session.dart';
import 'package:fieldops_ai/core/theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class SyncScreen extends ConsumerStatefulWidget {
  const SyncScreen({super.key});

  @override
  ConsumerState<SyncScreen> createState() => _SyncScreenState();
}

class _SyncScreenState extends ConsumerState<SyncScreen> {
  String? message;

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(sessionProvider);
    return Scaffold(
      appBar: AppBar(title: const Text('Sync status')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(session.offline ? 'Offline' : 'Online', style: const TextStyle(fontSize: 28, fontWeight: FontWeight.w800)),
            const SizedBox(height: 8),
            Text('${session.pendingSync} pending record(s)', style: const TextStyle(color: FieldOpsColors.muted)),
            const SizedBox(height: 16),
            const Text(
              'Every locally created inspection carries local_id, version and sync_status (PENDING / SYNCING / SYNCED / FAILED / CONFLICT).',
            ),
            const SizedBox(height: 20),
            FilledButton(
              onPressed: () async {
                final result = await ref.read(sessionProvider.notifier).syncNow();
                setState(() => message = result);
              },
              child: const Text('Synchronize now'),
            ),
            if (message != null) ...[
              const SizedBox(height: 16),
              Text(message!, style: const TextStyle(fontWeight: FontWeight.w600)),
            ],
          ],
        ),
      ),
    );
  }
}
