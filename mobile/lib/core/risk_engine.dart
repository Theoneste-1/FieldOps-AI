import 'package:fieldops_ai/core/models.dart';

/// Device-side copy of the deterministic risk engine.
/// The server remains the system of record; this lets inspectors see a score offline.
class RiskEngine {
  static RiskResult calculate({
    required List<Observation> observations,
    required List<Measurement> measurements,
    int previousFailures = 0,
  }) {
    final blob = observations
        .where((o) => o.valueBool == true || (o.valueText != null && !{'no', 'normal', 'ok', 'none'}.contains(o.valueText!.toLowerCase())))
        .map((o) => o.valueText ?? '')
        .join(' ')
        .toLowerCase();
    final breakdown = <Map<String, dynamic>>[];

    void fire(String key, String label, int points, String evidence) {
      if (breakdown.any((e) => e['key'] == key)) return;
      breakdown.add({'key': key, 'label': label, 'points': points, 'evidence': evidence});
    }

    final abnormal = <String>[];
    var tempAbnormal = false;
    for (final m in measurements) {
      final max = m.maxThreshold;
      if (max != null && m.value > max) {
        abnormal.add('${m.label}=${m.value}${m.unit}');
        if (m.fieldKey.contains('temp')) tempAbnormal = true;
      }
    }
    if (tempAbnormal || blob.contains('overheat') || blob.contains('hot')) {
      fire('temperature_abnormal', 'Temperature abnormality', 25, abnormal.join(', '));
    }
    if (observations.any((o) => o.category == 'leakage' && o.valueBool == true) ||
        blob.contains('oil around') ||
        blob.contains('leaking')) {
      fire('oil_leakage', 'Oil leakage', 25, 'Leakage observation present');
    }
    if (observations.any((o) => o.category == 'structural' && o.valueBool == true) || blob.contains('damage')) {
      fire('structural_damage', 'Structural damage', 20, 'Structural observation present');
    }
    if (observations.any((o) => o.category == 'noise') || blob.contains('noise') || blob.contains('high')) {
      final noise = observations.where((o) => o.fieldKey == 'noise').toList();
      if (noise.isNotEmpty && (noise.first.valueText ?? '').toLowerCase() != 'normal') {
        fire('abnormal_sound', 'Abnormal sound', 15, 'Noise observation present');
      }
    }
    if (previousFailures > 0) {
      fire('previous_failures', 'Previous failures', 15, '$previousFailures recent high/critical');
    }
    if (abnormal.isNotEmpty) {
      fire('out_of_range_measurement', 'Out-of-range measurement', 20, abnormal.join('; '));
    }
    if (observations.any((o) => o.fieldKey == 'immediate_danger' && o.valueBool == true)) {
      fire('immediate_danger', 'Immediate danger flag', 40, 'Flagged by inspector');
    }

    var score = breakdown.fold<int>(0, (sum, e) => sum + (e['points'] as int));
    if (score > 100) score = 100;
    if (breakdown.any((e) => e['key'] == 'immediate_danger') && score < 81) score = 81;
    final level = score <= 30
        ? 'low'
        : score <= 60
            ? 'medium'
            : score <= 80
                ? 'high'
                : 'critical';
    return RiskResult(score: score, level: level, breakdown: breakdown);
  }
}
