import 'package:fieldops_ai/core/session.dart';
import 'package:fieldops_ai/core/widgets.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class WorkOrdersScreen extends ConsumerWidget {
  const WorkOrdersScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final items = ref.watch(sessionProvider).workOrders;
    return Scaffold(
      appBar: AppBar(title: const Text('Work orders')),
      body: items.isEmpty
          ? const EmptyState(
              icon: Icons.assignment_outlined,
              title: 'No open work',
              body: 'Critical inspections can open a draft work order. A supervisor still assigns and verifies it.',
            )
          : ListView.separated(
              padding: const EdgeInsets.all(16),
              itemCount: items.length,
              separatorBuilder: (_, __) => const SizedBox(height: 8),
              itemBuilder: (context, index) {
                final item = items[index];
                return Card(
                  child: ListTile(
                    title: Text(item.title),
                    subtitle: Text('${item.assetCode ?? ''}  ·  ${item.status.replaceAll('_', ' ')}'),
                    trailing: RiskBadge(level: item.priority),
                  ),
                );
              },
            ),
    );
  }
}
