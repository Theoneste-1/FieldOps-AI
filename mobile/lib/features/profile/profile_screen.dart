import 'package:fieldops_ai/core/session.dart';
import 'package:fieldops_ai/core/theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class ProfileScreen extends ConsumerWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final session = ref.watch(sessionProvider);
    final user = session.user;
    return Scaffold(
      appBar: AppBar(title: const Text('More')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(user?.fullName ?? '', style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800)),
          Text('${user?.role.replaceAll('_', ' ')}  ·  ${user?.email}', style: const TextStyle(color: FieldOpsColors.muted)),
          const SizedBox(height: 16),
          ListTile(leading: const Icon(Icons.fact_check_outlined), title: const Text('Inspections'), onTap: () => context.go('/inspections')),
          ListTile(leading: const Icon(Icons.insights_outlined), title: const Text('Analytics'), onTap: () => context.go('/analytics')),
          ListTile(leading: const Icon(Icons.notifications_outlined), title: const Text('Notifications'), onTap: () => context.go('/notifications')),
          ListTile(leading: const Icon(Icons.cloud_sync_outlined), title: const Text('Offline queue / sync'), onTap: () => context.go('/sync')),
          const Divider(),
          const ListTile(
            leading: Icon(Icons.security_outlined),
            title: Text('Gemini key stays on the backend'),
            subtitle: Text('The APK never embeds the model credential.'),
          ),
          ListTile(
            leading: const Icon(Icons.logout),
            title: const Text('Sign out'),
            onTap: () => ref.read(sessionProvider.notifier).logout(),
          ),
        ],
      ),
    );
  }
}
