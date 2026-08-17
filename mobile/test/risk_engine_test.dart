import 'package:fieldops_ai/core/risk_engine.dart';
import 'package:fieldops_ai/core/models.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  test('T-104 wow-demo inputs score critical', () {
    final result = RiskEngine.calculate(
      observations: [
        Observation(fieldKey: 'oil_leakage', label: 'Oil leakage', category: 'leakage', valueBool: true, valueText: 'Yes'),
        Observation(fieldKey: 'noise', label: 'Noise', category: 'noise', valueText: 'high'),
        Observation(fieldKey: 'visual_damage', label: 'Visual damage', category: 'structural', valueBool: true, valueText: 'Yes'),
      ],
      measurements: [
        Measurement(fieldKey: 'temperature', label: 'Temperature', value: 91, unit: '°C', maxThreshold: 80),
      ],
      previousFailures: 1,
    );
    expect(result.score >= 81, true);
    expect(result.level, 'critical');
  });
}
