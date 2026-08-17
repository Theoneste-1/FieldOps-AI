import 'dart:convert';

import 'package:fieldops_ai/core/models.dart';
import 'package:fieldops_ai/core/risk_engine.dart';
import 'package:uuid/uuid.dart';

class DemoCatalog {
  static List<FieldAsset> assets() => [
        _a('T-101', 'Sandton TX 1', 'low', 18, -26.1070, 28.0550, 'Sandton Substation'),
        _a('T-102', 'Sandton TX 2', 'medium', 44, -26.1082, 28.0581, 'Sandton Substation'),
        _a('T-103', 'Midrand TX 1', 'low', 12, -25.9984, 28.1244, 'Midrand Switching Yard'),
        _a('T-104', 'Midrand TX 4 — Critical demo', 'high', 72, -25.9998, 28.1288, 'Midrand Switching Yard'),
        _a('T-105', 'Alexandra TX 1', 'medium', 51, -26.1028, 28.0971, 'Alexandra Feeder Hub'),
        _a('T-106', 'Alexandra TX 2', 'low', 22, -26.1049, 28.1012, 'Alexandra Feeder Hub'),
        _a('T-107', 'Rosebank TX 1', 'low', 9, -26.1442, 28.0402, 'Rosebank Distribution'),
        _a('T-108', 'Rosebank TX 2', 'high', 68, -26.1461, 28.0433, 'Rosebank Distribution'),
        _a('SG-12', 'Sandton Bay 12', 'medium', 40, -26.1064, 28.0574, 'Sandton Substation'),
        _a('PL-441', 'Alexandra Pole 441', 'medium', 38, -26.1058, 28.0960, 'Alexandra Feeder Hub'),
      ];

  static FieldAsset _a(String code, String name, String risk, int score, double lat, double lng, String loc) {
    return FieldAsset(
      id: 'demo-$code',
      code: code,
      name: name,
      riskLevel: risk,
      riskScore: score,
      latitude: lat,
      longitude: lng,
      typeName: code.startsWith('T') ? 'Distribution Transformer' : 'Field asset',
      locationName: loc,
      status: 'active',
      lastInspectionAt: DateTime.now().subtract(const Duration(days: 10)).toIso8601String(),
    );
  }

  static UserAccount userFor(String email) {
    const people = {
      'inspector@fieldops.ai': ['Thabo Mokoena', 'inspector', 'INS-014'],
      'supervisor@fieldops.ai': ['Lerato Dlamini', 'supervisor', 'SUP-007'],
      'manager@fieldops.ai': ['Pieter van Wyk', 'operations_manager', 'OPS-001'],
      'admin@fieldops.ai': ['Nomsa Khumalo', 'admin', 'ADM-001'],
    };
    final row = people[email] ?? ['Demo User', 'inspector', 'DEMO'];
    return UserAccount(id: 'demo-user', email: email, fullName: row[0], role: row[1], employeeCode: row[2], organizationId: 'helios');
  }

  static InspectionRecord wowInspection(FieldAsset asset, List<Observation> observations, List<Measurement> measurements, String notes) {
    final risk = RiskEngine.calculate(observations: observations, measurements: measurements, previousFailures: 1);
    final ai = AiInsight(
      summary:
          'Deterministic risk is ${risk.level.toUpperCase()} (${risk.score}/100). Potential equipment degradation detected from elevated temperature, oil leakage and abnormal noise.',
      causes: [
        'Potential seal failure',
        'Potential overheating / cooling degradation',
        'Potential mechanical degradation',
      ],
      recommendations: [
        'Immediate technical inspection by a qualified supervisor',
        'Check oil sealing system',
        'Verify operating temperature against nameplate limits',
      ],
      brief: '${asset.code}: ${risk.level} risk. AI assistance is advisory; it did not change the risk score.',
      confidence: 0.78,
      severity: risk.level,
      usedFallback: true,
    );
    return InspectionRecord(
      id: const Uuid().v4(),
      assetId: asset.id,
      status: 'analyzed',
      assetCode: asset.code,
      assetName: asset.name,
      notes: notes,
      observations: observations,
      measurements: measurements,
      risk: risk,
      ai: ai,
      localId: const Uuid().v4(),
      syncStatus: 'pending',
      createdAt: DateTime.now().toIso8601String(),
    );
  }

  static String encodeQueue(List<Map<String, dynamic>> items) => jsonEncode(items);
}
