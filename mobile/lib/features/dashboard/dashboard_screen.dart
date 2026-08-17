import 'package:fieldops_ai/core/session.dart';
import 'package:fieldops_ai/core/theme.dart';
import 'package:fieldops_ai/core/widgets.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final session = ref.watch(sessionProvider);
    final kpis = session.kpis;
    return Scaffold(
      appBar: AppBar(
        title: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(session.user?.fullName ?? 'FieldOps'),
            Text(
              session.user?.role.replaceAll('_', ' ') ?? '',
              style: const TextStyle(fontSize: 12, color: FieldOpsColors.muted, fontWeight: FontWeight.w500),
            ),
          ],
        ),
        actions: [
          IconButton(onPressed: () => context.go('/notifications'), icon: const Icon(Icons.notifications_outlined)),
          IconButton(onPressed: () => ref.read(sessionProvider.notifier).refresh(), icon: const Icon(Icons.refresh)),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () => ref.read(sessionProvider.notifier).refresh(),
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            OfflineBanner(offline: session.offline, pending: session.pendingSync),
            const Text('Operations snapshot', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
            const SizedBox(height: 12),
            GridView.count(
              crossAxisCount: 2,
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              mainAxisSpacing: 12,
              crossAxisSpacing: 12,
              childAspectRatio: 1.25,
              children: [
                KpiCard(label: 'Inspections', value: '${kpis?.inspectionsTotal ?? 0}'),
                KpiCard(label: 'Critical', value: '${kpis?.critical ?? 0}', accent: FieldOpsColors.critical),
                KpiCard(label: 'Open issues', value: '${kpis?.openIssues ?? 0}', accent: FieldOpsColors.high),
                KpiCard(label: 'Resolved', value: '${(kpis?.resolvedRate ?? 0).toStringAsFixed(0)}%'),
              ],
            ),
            const SizedBox(height: 20),
            const Text('Continue the demo', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
            const SizedBox(height: 8),
            Card(
              child: ListTile(
                leading: const CircleAvatar(backgroundColor: FieldOpsColors.critical, child: Text('T', style: TextStyle(color: Colors.white))),
                title: const Text('Inspect transformer T-104'),
                subtitle: const Text('Midrand · temperature trend climbing'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () {
                  final asset = session.assets.where((a) => a.code == 'T-104');
                  if (asset.isNotEmpty) {
                    context.go('/assets/${asset.first.id}');
                  } else {
                    context.go('/map');
                  }
                },
              ),
            ),
            ListTile(
              leading: const Icon(Icons.map_outlined),
              title: const Text('Open asset map'),
              onTap: () => context.go('/map'),
            ),
            ListTile(
              leading: const Icon(Icons.insights_outlined),
              title: const Text('Analytics'),
              onTap: () => context.go('/analytics'),
            ),
            ListTile(
              leading: const Icon(Icons.cloud_sync_outlined),
              title: Text('Sync status · ${session.pendingSync} pending'),
              onTap: () => context.go('/sync'),
            ),
          ],
        ),
      ),
    );
  }
}
