import 'package:fieldops_ai/core/session.dart';
import 'package:fieldops_ai/core/widgets.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class AssetListScreen extends ConsumerStatefulWidget {
  const AssetListScreen({super.key});

  @override
  ConsumerState<AssetListScreen> createState() => _AssetListScreenState();
}

class _AssetListScreenState extends ConsumerState<AssetListScreen> {
  String query = '';

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(sessionProvider);
    final assets = session.assets.where((a) {
      if (query.isEmpty) return true;
      return a.code.toLowerCase().contains(query.toLowerCase()) || a.name.toLowerCase().contains(query.toLowerCase());
    }).toList();
    return Scaffold(
      appBar: AppBar(title: const Text('Assets')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextField(
              decoration: const InputDecoration(prefixIcon: Icon(Icons.search), hintText: 'Search code or name'),
              onChanged: (value) => setState(() => query = value),
            ),
          ),
          Expanded(
            child: ListView.separated(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              itemCount: assets.length,
              separatorBuilder: (_, __) => const SizedBox(height: 8),
              itemBuilder: (context, index) {
                final asset = assets[index];
                return Card(
                  child: ListTile(
                    title: Text('${asset.code}  ·  ${asset.name}'),
                    subtitle: Text(asset.locationName ?? asset.typeName ?? ''),
                    trailing: RiskBadge(level: asset.riskLevel, score: asset.riskScore),
                    onTap: () => context.go('/assets/${asset.id}'),
                  ),
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
