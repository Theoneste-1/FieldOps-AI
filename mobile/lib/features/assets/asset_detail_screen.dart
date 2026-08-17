import 'package:collection/collection.dart';
import 'package:fieldops_ai/core/session.dart';
import 'package:fieldops_ai/core/widgets.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class AssetDetailScreen extends ConsumerWidget {
  const AssetDetailScreen({super.key, required this.assetId});

  final String assetId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final session = ref.watch(sessionProvider);
    final asset = session.assets.where((a) => a.id == assetId).firstOrNull;
    if (asset == null) {
      return const Scaffold(body: Center(child: Text('Asset not found')));
    }
    final history = session.inspections.where((i) => i.assetId == asset.id).toList();
    return Scaffold(
      appBar: AppBar(title: Text(asset.code)),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.go('/inspect/${asset.id}'),
        icon: const Icon(Icons.playlist_add_check),
        label: const Text('Start inspection'),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(asset.name, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800)),
          const SizedBox(height: 8),
          Wrap(spacing: 8, children: [RiskBadge(level: asset.riskLevel, score: asset.riskScore), Chip(label: Text(asset.status))]),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _row('Type', asset.typeName ?? '—'),
                  _row('Location', asset.locationName ?? '—'),
                  _row('Last inspection', asset.lastInspectionAt?.split('T').first ?? '—'),
                  _row('Coordinates', asset.latitude == null ? '—' : '${asset.latitude!.toStringAsFixed(4)}, ${asset.longitude!.toStringAsFixed(4)}'),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          const Text('Inspection history', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
          const SizedBox(height: 8),
          if (history.isEmpty)
            const EmptyState(icon: Icons.history, title: 'No inspections on this device yet', body: 'Start the T-104 inspection to generate risk, AI analysis and a work order.')
          else
            ...history.map(
              (item) => Card(
                child: ListTile(
                  title: Text(item.status.replaceAll('_', ' ')),
                  subtitle: Text(item.notes ?? item.createdAt ?? ''),
                  trailing: item.risk == null ? null : RiskBadge(level: item.risk!.level, score: item.risk!.score),
                  onTap: () => context.go('/inspections/${item.id}'),
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _row(String k, String v) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8),
      child: Row(
        children: [
          SizedBox(width: 130, child: Text(k, style: const TextStyle(color: Colors.black54))),
          Expanded(child: Text(v, style: const TextStyle(fontWeight: FontWeight.w700))),
        ],
      ),
    );
  }
}
