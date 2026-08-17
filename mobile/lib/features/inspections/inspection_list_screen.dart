import 'package:fieldops_ai/core/session.dart';
import 'package:fieldops_ai/core/widgets.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class InspectionListScreen extends ConsumerWidget {
  const InspectionListScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final items = ref.watch(sessionProvider).inspections;
    return Scaffold(
      appBar: AppBar(title: const Text('Inspections')),
      body: items.isEmpty
          ? const EmptyState(icon: Icons.fact_check_outlined, title: 'No inspections yet', body: 'Start from the map or asset list.')
          : ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: items.length,
              separatorBuilder: (_, __) => const SizedBox(height: 8),
              itemBuilder: (context, index) {
                final item = items[index];
                return Card(
                  child: ListTile(
                    title: Text(item.assetCode ?? item.id),
                    subtitle: Text('${item.status.replaceAll('_', ' ')}  ·  ${item.syncStatus}'),
                    trailing: item.risk == null ? null : RiskBadge(level: item.risk!.level, score: item.risk!.score),
                    onTap: () => context.go('/inspections/${item.id}'),
                  ),
                );
              },
            ),
    );
  }
}
