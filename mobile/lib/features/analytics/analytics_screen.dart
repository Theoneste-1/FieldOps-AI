import 'package:fieldops_ai/core/session.dart';
import 'package:fieldops_ai/core/theme.dart';
import 'package:fieldops_ai/core/widgets.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class AnalyticsScreen extends ConsumerWidget {
  const AnalyticsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final session = ref.watch(sessionProvider);
    final kpis = session.kpis;
    final dist = session.riskDistribution.isEmpty
        ? [NamedCountProxy('low', 6), NamedCountProxy('medium', 3), NamedCountProxy('high', 2), NamedCountProxy('critical', 1)]
        : session.riskDistribution.map((e) => NamedCountProxy(e.name, e.count)).toList();
    return Scaffold(
      appBar: AppBar(title: const Text('Analytics')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            mainAxisSpacing: 12,
            crossAxisSpacing: 12,
            childAspectRatio: 1.3,
            children: [
              KpiCard(label: 'Inspections', value: '${kpis?.inspectionsTotal ?? 0}'),
              KpiCard(label: 'Critical', value: '${kpis?.critical ?? 0}', accent: FieldOpsColors.critical),
              KpiCard(label: 'Open WO', value: '${kpis?.openWorkOrders ?? 0}'),
              KpiCard(label: 'Avg risk', value: (kpis?.averageRisk ?? 0).toStringAsFixed(0)),
            ],
          ),
          const SizedBox(height: 24),
          const Text('Risk distribution', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
          const SizedBox(height: 12),
          SizedBox(
            height: 200,
            child: PieChart(
              PieChartData(
                sections: dist.map((item) {
                  return PieChartSectionData(
                    value: item.count.toDouble(),
                    title: item.name,
                    color: FieldOpsColors.risk(item.name),
                    radius: 60,
                    titleStyle: const TextStyle(fontSize: 11, color: Colors.white, fontWeight: FontWeight.w700),
                  );
                }).toList(),
              ),
            ),
          ),
          const SizedBox(height: 16),
          const Text('Issues by category', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800)),
          ...session.issueCategories.map(
            (item) => ListTile(title: Text(item.name), trailing: Text('${item.count}', style: const TextStyle(fontWeight: FontWeight.w800))),
          ),
        ],
      ),
    );
  }
}

class NamedCountProxy {
  NamedCountProxy(this.name, this.count);
  final String name;
  final int count;
}
