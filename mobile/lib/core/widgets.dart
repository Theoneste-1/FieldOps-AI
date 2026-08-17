import 'package:fieldops_ai/core/theme.dart';
import 'package:flutter/material.dart';

class RiskBadge extends StatelessWidget {
  const RiskBadge({super.key, required this.level, this.score});

  final String level;
  final int? score;

  @override
  Widget build(BuildContext context) {
    final color = FieldOpsColors.risk(level);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.15),
        borderRadius: BorderRadius.circular(99),
        border: Border.all(color: color.withValues(alpha: 0.4)),
      ),
      child: Text(
        score == null ? level.toUpperCase() : '${level.toUpperCase()}  $score',
        style: TextStyle(color: color, fontWeight: FontWeight.w800, fontSize: 11, letterSpacing: 0.4),
      ),
    );
  }
}

class KpiCard extends StatelessWidget {
  const KpiCard({super.key, required this.label, required this.value, this.hint, this.accent});

  final String label;
  final String value;
  final String? hint;
  final Color? accent;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: FieldOpsColors.surface,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: FieldOpsColors.line),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(label.toUpperCase(), style: const TextStyle(fontSize: 11, letterSpacing: 1.1, color: FieldOpsColors.muted, fontWeight: FontWeight.w700)),
          const SizedBox(height: 8),
          Text(value, style: TextStyle(fontSize: 28, fontWeight: FontWeight.w800, color: accent ?? FieldOpsColors.ink)),
          if (hint != null) ...[
            const SizedBox(height: 4),
            Text(hint!, style: const TextStyle(color: FieldOpsColors.muted, fontSize: 12)),
          ],
        ],
      ),
    );
  }
}

class EmptyState extends StatelessWidget {
  const EmptyState({super.key, required this.icon, required this.title, required this.body});

  final IconData icon;
  final String title;
  final String body;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.all(32),
      child: Column(
        children: [
          Icon(icon, size: 42, color: FieldOpsColors.muted),
          const SizedBox(height: 12),
          Text(title, style: const TextStyle(fontWeight: FontWeight.w800, fontSize: 18)),
          const SizedBox(height: 6),
          Text(body, textAlign: TextAlign.center, style: const TextStyle(color: FieldOpsColors.muted)),
        ],
      ),
    );
  }
}

class OfflineBanner extends StatelessWidget {
  const OfflineBanner({super.key, required this.offline, this.pending = 0});

  final bool offline;
  final int pending;

  @override
  Widget build(BuildContext context) {
    if (!offline && pending == 0) return const SizedBox.shrink();
    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 12),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFFFF3D6),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        offline
            ? 'No internet. Your work is saved locally and will synchronize when connectivity returns.'
            : '$pending record(s) waiting to synchronize.',
        style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
      ),
    );
  }
}
