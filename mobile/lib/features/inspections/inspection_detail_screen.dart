import 'package:collection/collection.dart';
import 'package:fieldops_ai/core/session.dart';
import 'package:fieldops_ai/core/theme.dart';
import 'package:fieldops_ai/core/widgets.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class InspectionDetailScreen extends ConsumerWidget {
  const InspectionDetailScreen({super.key, required this.inspectionId});

  final String inspectionId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final session = ref.watch(sessionProvider);
    final item = session.inspections.where((i) => i.id == inspectionId).firstOrNull;
    if (item == null) {
      return const Scaffold(body: Center(child: Text('Inspection not found')));
    }
    final risk = item.risk;
    final ai = item.ai;
    return Scaffold(
      appBar: AppBar(title: Text(item.assetCode ?? 'Inspection')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          if (item.syncStatus == 'pending')
            const OfflineBanner(offline: true),
          Text(item.assetName ?? '', style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800)),
          const SizedBox(height: 8),
          Wrap(spacing: 8, children: [
            Chip(label: Text(item.status.replaceAll('_', ' '))),
            if (risk != null) RiskBadge(level: risk.level, score: risk.score),
          ]),
          const SizedBox(height: 16),
          if (risk != null)
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text('Deterministic risk engine', style: TextStyle(fontWeight: FontWeight.w800, fontSize: 16)),
                    const SizedBox(height: 8),
                    Text('${risk.score} / 100', style: TextStyle(fontSize: 36, fontWeight: FontWeight.w800, color: FieldOpsColors.risk(risk.level))),
                    const SizedBox(height: 8),
                    ...risk.breakdown.map((row) => ListTile(
                          dense: true,
                          contentPadding: EdgeInsets.zero,
                          title: Text('${row['label']}'),
                          trailing: Text('+${row['points']}'),
                          subtitle: Text('${row['evidence'] ?? ''}'),
                        )),
                  ],
                ),
              ),
            ),
          const SizedBox(height: 12),
          if (ai != null)
            Card(
              color: FieldOpsColors.primary,
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: DefaultTextStyle(
                  style: const TextStyle(color: Colors.white),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(ai.usedFallback ? 'AI INSIGHT  ·  heuristic fallback' : 'AI INSIGHT  ·  Gemini', style: const TextStyle(letterSpacing: 1, fontWeight: FontWeight.w800, fontSize: 12)),
                      const SizedBox(height: 10),
                      Text(ai.summary, style: const TextStyle(fontSize: 16, height: 1.4, fontWeight: FontWeight.w600)),
                      const SizedBox(height: 14),
                      const Text('Possible causes', style: TextStyle(fontWeight: FontWeight.w800)),
                      ...ai.causes.map((c) => Padding(padding: const EdgeInsets.only(top: 6), child: Text('• $c'))),
                      const SizedBox(height: 14),
                      const Text('Recommended', style: TextStyle(fontWeight: FontWeight.w800)),
                      ...ai.recommendations.asMap().entries.map((e) => Padding(padding: const EdgeInsets.only(top: 6), child: Text('${e.key + 1}. ${e.value}'))),
                      const SizedBox(height: 12),
                      const Text('AI does not shut down equipment, classify emergencies, or approve work.', style: TextStyle(color: Colors.white70, fontSize: 12)),
                    ],
                  ),
                ),
              ),
            )
          else
            const Card(
              child: ListTile(
                title: Text('AI analysis temporarily unavailable.'),
                subtitle: Text('Your inspection has been saved. Analysis will be retried automatically.'),
              ),
            ),
          const SizedBox(height: 16),
          FilledButton(
            onPressed: () => context.go('/work-orders'),
            child: const Text('View work orders'),
          ),
          const SizedBox(height: 8),
          OutlinedButton(
            onPressed: () => context.go('/analytics'),
            child: const Text('Open analytics'),
          ),
        ],
      ),
    );
  }
}
