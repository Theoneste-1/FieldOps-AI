class UserAccount {
  UserAccount({
    required this.id,
    required this.email,
    required this.fullName,
    required this.role,
    this.organizationId = '',
    this.phone,
    this.employeeCode,
  });

  final String id;
  final String email;
  final String fullName;
  final String role;
  final String organizationId;
  final String? phone;
  final String? employeeCode;

  factory UserAccount.fromJson(Map<String, dynamic> json) => UserAccount(
        id: json['id'] as String,
        email: json['email'] as String,
        fullName: json['full_name'] as String? ?? json['fullName'] as String,
        role: json['role'] as String,
        organizationId: json['organization_id'] as String? ?? '',
        phone: json['phone'] as String?,
        employeeCode: json['employee_code'] as String?,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'email': email,
        'full_name': fullName,
        'role': role,
        'organization_id': organizationId,
        'phone': phone,
        'employee_code': employeeCode,
      };
}

class FieldAsset {
  FieldAsset({
    required this.id,
    required this.code,
    required this.name,
    required this.riskLevel,
    required this.riskScore,
    this.description,
    this.status = 'active',
    this.latitude,
    this.longitude,
    this.typeName,
    this.locationName,
    this.lastInspectionAt,
  });

  final String id;
  final String code;
  final String name;
  final String riskLevel;
  final int riskScore;
  final String? description;
  final String status;
  final double? latitude;
  final double? longitude;
  final String? typeName;
  final String? locationName;
  final String? lastInspectionAt;

  factory FieldAsset.fromJson(Map<String, dynamic> json) => FieldAsset(
        id: json['id'] as String,
        code: json['code'] as String,
        name: json['name'] as String,
        riskLevel: json['current_risk_level'] as String? ?? 'low',
        riskScore: (json['current_risk_score'] as num?)?.toInt() ?? 0,
        description: json['description'] as String?,
        status: json['status'] as String? ?? 'active',
        latitude: (json['latitude'] as num?)?.toDouble(),
        longitude: (json['longitude'] as num?)?.toDouble(),
        typeName: json['asset_type'] is Map ? json['asset_type']['name'] as String? : json['asset_type_name'] as String?,
        locationName: json['location'] is Map ? json['location']['name'] as String? : json['location_name'] as String?,
        lastInspectionAt: json['last_inspection_at'] as String?,
      );
}

class Observation {
  Observation({
    required this.fieldKey,
    required this.label,
    required this.category,
    this.valueText,
    this.valueBool,
    this.severity,
  });

  final String fieldKey;
  final String label;
  final String category;
  final String? valueText;
  final bool? valueBool;
  final String? severity;

  Map<String, dynamic> toJson() => {
        'field_key': fieldKey,
        'label': label,
        'category': category,
        'value_text': valueText,
        'value_bool': valueBool,
        'severity': severity,
      };

  factory Observation.fromJson(Map<String, dynamic> json) => Observation(
        fieldKey: json['field_key'] as String? ?? '',
        label: json['label'] as String? ?? '',
        category: json['category'] as String? ?? 'other',
        valueText: json['value_text'] as String?,
        valueBool: json['value_bool'] as bool?,
        severity: json['severity'] as String?,
      );
}

class Measurement {
  Measurement({
    required this.fieldKey,
    required this.label,
    required this.value,
    this.unit = '',
    this.maxThreshold,
    this.isAbnormal = false,
  });

  final String fieldKey;
  final String label;
  final double value;
  final String unit;
  final double? maxThreshold;
  final bool isAbnormal;

  Map<String, dynamic> toJson() => {
        'field_key': fieldKey,
        'label': label,
        'value': value,
        'unit': unit,
        'max_threshold': maxThreshold,
      };

  factory Measurement.fromJson(Map<String, dynamic> json) => Measurement(
        fieldKey: json['field_key'] as String? ?? '',
        label: json['label'] as String? ?? '',
        value: (json['value'] as num?)?.toDouble() ?? 0,
        unit: json['unit'] as String? ?? '',
        maxThreshold: (json['max_threshold'] as num?)?.toDouble(),
        isAbnormal: json['is_abnormal'] as bool? ?? false,
      );
}

class RiskResult {
  RiskResult({required this.score, required this.level, required this.breakdown});

  final int score;
  final String level;
  final List<Map<String, dynamic>> breakdown;
}

class AiInsight {
  AiInsight({
    required this.summary,
    required this.causes,
    required this.recommendations,
    this.brief,
    this.confidence,
    this.severity,
    this.usedFallback = false,
    this.status = 'completed',
  });

  final String summary;
  final List<String> causes;
  final List<String> recommendations;
  final String? brief;
  final double? confidence;
  final String? severity;
  final bool usedFallback;
  final String status;

  factory AiInsight.fromJson(Map<String, dynamic> json) => AiInsight(
        summary: json['risk_summary'] as String? ?? '',
        causes: ((json['possible_causes'] as List?) ?? const []).map((e) => '$e').toList(),
        recommendations: ((json['recommendations'] as List?) ?? const []).map((e) => '$e').toList(),
        brief: json['supervisor_brief'] as String?,
        confidence: (json['confidence'] as num?)?.toDouble(),
        severity: json['severity'] as String?,
        usedFallback: json['used_fallback'] as bool? ?? false,
        status: json['status'] as String? ?? 'completed',
      );
}

class InspectionRecord {
  InspectionRecord({
    required this.id,
    required this.assetId,
    required this.status,
    this.assetCode,
    this.assetName,
    this.notes,
    this.observations = const [],
    this.measurements = const [],
    this.risk,
    this.ai,
    this.localId,
    this.syncStatus = 'synced',
    this.createdAt,
  });

  final String id;
  final String assetId;
  final String status;
  final String? assetCode;
  final String? assetName;
  final String? notes;
  final List<Observation> observations;
  final List<Measurement> measurements;
  final RiskResult? risk;
  final AiInsight? ai;
  final String? localId;
  final String syncStatus;
  final String? createdAt;

  factory InspectionRecord.fromJson(Map<String, dynamic> json) {
    final asset = json['asset'];
    final riskJson = json['risk_assessment'];
    final aiJson = json['ai_analysis'];
    return InspectionRecord(
      id: json['id'] as String,
      assetId: json['asset_id'] as String? ?? '',
      status: json['status'] as String? ?? 'draft',
      assetCode: asset is Map ? asset['code'] as String? : json['asset_code'] as String?,
      assetName: asset is Map ? asset['name'] as String? : json['asset_name'] as String?,
      notes: json['notes'] as String?,
      observations: ((json['observations'] as List?) ?? const [])
          .map((e) => Observation.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList(),
      measurements: ((json['measurements'] as List?) ?? const [])
          .map((e) => Measurement.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList(),
      risk: riskJson is Map
          ? RiskResult(
              score: (riskJson['score'] as num?)?.toInt() ?? 0,
              level: riskJson['level'] as String? ?? 'low',
              breakdown: ((riskJson['breakdown'] as List?) ?? const []).map((e) => Map<String, dynamic>.from(e as Map)).toList(),
            )
          : null,
      ai: aiJson is Map ? AiInsight.fromJson(Map<String, dynamic>.from(aiJson)) : null,
      localId: json['local_id'] as String?,
      syncStatus: json['sync_status'] as String? ?? 'synced',
      createdAt: json['created_at'] as String?,
    );
  }
}

class WorkOrderRecord {
  WorkOrderRecord({
    required this.id,
    required this.title,
    required this.priority,
    required this.status,
    this.assetCode,
    this.description,
    this.dueAt,
  });

  final String id;
  final String title;
  final String priority;
  final String status;
  final String? assetCode;
  final String? description;
  final String? dueAt;

  factory WorkOrderRecord.fromJson(Map<String, dynamic> json) => WorkOrderRecord(
        id: json['id'] as String,
        title: json['title'] as String,
        priority: json['priority'] as String? ?? 'medium',
        status: json['status'] as String? ?? 'open',
        assetCode: json['asset'] is Map ? json['asset']['code'] as String? : json['asset_code'] as String?,
        description: json['description'] as String?,
        dueAt: json['due_at'] as String?,
      );
}

class KpiSnapshot {
  KpiSnapshot({
    this.inspectionsTotal = 0,
    this.critical = 0,
    this.openIssues = 0,
    this.resolvedRate = 0,
    this.openWorkOrders = 0,
    this.averageRisk = 0,
  });

  final int inspectionsTotal;
  final int critical;
  final int openIssues;
  final double resolvedRate;
  final int openWorkOrders;
  final double averageRisk;

  factory KpiSnapshot.fromJson(Map<String, dynamic> json) => KpiSnapshot(
        inspectionsTotal: json['inspections_total'] as int? ?? 0,
        critical: json['critical_inspections'] as int? ?? 0,
        openIssues: json['open_issues'] as int? ?? 0,
        resolvedRate: (json['resolved_rate'] as num?)?.toDouble() ?? 0,
        openWorkOrders: json['open_work_orders'] as int? ?? 0,
        averageRisk: (json['average_risk'] as num?)?.toDouble() ?? 0,
      );
}

class AppNotification {
  AppNotification({
    required this.id,
    required this.title,
    required this.body,
    this.read = false,
    this.createdAt,
  });

  final String id;
  final String title;
  final String body;
  final bool read;
  final String? createdAt;

  factory AppNotification.fromJson(Map<String, dynamic> json) => AppNotification(
        id: json['id'] as String,
        title: json['title'] as String,
        body: json['body'] as String,
        read: json['read_at'] != null,
        createdAt: json['created_at'] as String?,
      );
}

class NamedCount {
  NamedCount(this.name, this.count);
  final String name;
  final int count;
}
