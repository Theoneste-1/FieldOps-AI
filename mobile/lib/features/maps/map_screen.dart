import 'package:fieldops_ai/core/session.dart';
import 'package:fieldops_ai/core/theme.dart';
import 'package:fieldops_ai/core/widgets.dart';
import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:latlong2/latlong.dart';

class MapScreen extends ConsumerStatefulWidget {
  const MapScreen({super.key});

  @override
  ConsumerState<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends ConsumerState<MapScreen> {
  String filter = 'all';

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(sessionProvider);
    final assets = session.assets.where((a) => a.latitude != null && a.longitude != null).where((a) {
      if (filter == 'all') return true;
      return a.riskLevel == filter;
    }).toList();
    return Scaffold(
      appBar: AppBar(title: const Text('Asset map')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 8),
            child: Wrap(
              spacing: 8,
              children: ['all', 'critical', 'high', 'medium', 'low'].map((item) {
                return ChoiceChip(
                  label: Text(item.toUpperCase()),
                  selected: filter == item,
                  onSelected: (_) => setState(() => filter = item),
                );
              }).toList(),
            ),
          ),
          Expanded(
            child: FlutterMap(
              options: const MapOptions(initialCenter: LatLng(-26.08, 28.08), initialZoom: 11.2),
              children: [
                TileLayer(
                  urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                  userAgentPackageName: 'ai.fieldops.fieldops_ai',
                ),
                MarkerLayer(
                  markers: assets.map((asset) {
                    final color = FieldOpsColors.risk(asset.riskLevel);
                    return Marker(
                      point: LatLng(asset.latitude!, asset.longitude!),
                      width: 44,
                      height: 44,
                      child: GestureDetector(
                        onTap: () => context.go('/assets/${asset.id}'),
                        child: CircleAvatar(
                          backgroundColor: color,
                          child: Text(asset.code.substring(0, 1), style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w800)),
                        ),
                      ),
                    );
                  }).toList(),
                ),
              ],
            ),
          ),
          SizedBox(
            height: 118,
            child: ListView.separated(
              padding: const EdgeInsets.all(12),
              scrollDirection: Axis.horizontal,
              itemCount: assets.length,
              separatorBuilder: (_, __) => const SizedBox(width: 8),
              itemBuilder: (context, index) {
                final asset = assets[index];
                return SizedBox(
                  width: 220,
                  child: Card(
                    child: ListTile(
                      title: Text(asset.code),
                      subtitle: Text(asset.name, maxLines: 1, overflow: TextOverflow.ellipsis),
                      trailing: RiskBadge(level: asset.riskLevel, score: asset.riskScore),
                      onTap: () => context.go('/assets/${asset.id}'),
                    ),
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
