import 'package:dio/dio.dart';
import 'package:fieldops_ai/core/models.dart';

class ApiException implements Exception {
  ApiException(this.message);
  final String message;
  @override
  String toString() => message;
}

class FieldOpsApi {
  FieldOpsApi({required String baseUrl, String? token})
      : _dio = Dio(
          BaseOptions(
            baseUrl: '$baseUrl/api/v1',
            connectTimeout: const Duration(seconds: 8),
            receiveTimeout: const Duration(seconds: 30),
            headers: {
              if (token != null) 'Authorization': 'Bearer $token',
              'Content-Type': 'application/json',
            },
          ),
        );

  final Dio _dio;

  Future<Map<String, dynamic>> login(String email, String password, String deviceId) async {
    try {
      final response = await _dio.post('/auth/login', data: {
        'email': email,
        'password': password,
        'device_id': deviceId,
      });
      return Map<String, dynamic>.from(response.data as Map);
    } on DioException catch (e) {
      throw ApiException(_message(e));
    }
  }

  Future<List<FieldAsset>> assets({String? risk, String? q}) async {
    final response = await _dio.get('/assets', queryParameters: {
      if (risk != null) 'risk': risk,
      if (q != null && q.isNotEmpty) 'q': q,
    });
    return (response.data as List).map((e) => FieldAsset.fromJson(Map<String, dynamic>.from(e as Map))).toList();
  }

  Future<FieldAsset> asset(String id) async {
    final response = await _dio.get('/assets/$id');
    return FieldAsset.fromJson(Map<String, dynamic>.from(response.data as Map));
  }

  Future<List<InspectionRecord>> inspections({String? assetId, String? status}) async {
    final response = await _dio.get('/inspections', queryParameters: {
      if (assetId != null) 'asset_id': assetId,
      if (status != null) 'status': status,
    });
    return (response.data as List).map((e) => InspectionRecord.fromJson(Map<String, dynamic>.from(e as Map))).toList();
  }

  Future<InspectionRecord> createInspection(Map<String, dynamic> payload) async {
    final response = await _dio.post('/inspections', data: payload);
    return InspectionRecord.fromJson(Map<String, dynamic>.from(response.data as Map));
  }

  Future<InspectionRecord> submitInspection(String id) async {
    final response = await _dio.post('/inspections/$id/submit');
    return InspectionRecord.fromJson(Map<String, dynamic>.from(response.data as Map));
  }

  Future<InspectionRecord> inspection(String id) async {
    final response = await _dio.get('/inspections/$id');
    return InspectionRecord.fromJson(Map<String, dynamic>.from(response.data as Map));
  }

  Future<List<WorkOrderRecord>> workOrders() async {
    final response = await _dio.get('/work-orders');
    return (response.data as List).map((e) => WorkOrderRecord.fromJson(Map<String, dynamic>.from(e as Map))).toList();
  }

  Future<WorkOrderRecord> createWorkOrder(Map<String, dynamic> payload) async {
    final response = await _dio.post('/work-orders', data: payload);
    return WorkOrderRecord.fromJson(Map<String, dynamic>.from(response.data as Map));
  }

  Future<KpiSnapshot> kpis() async {
    final response = await _dio.get('/analytics/kpis');
    return KpiSnapshot.fromJson(Map<String, dynamic>.from(response.data as Map));
  }

  Future<List<NamedCount>> riskDistribution() async {
    final response = await _dio.get('/analytics/risk-distribution');
    return (response.data as List)
        .map((e) => NamedCount(e['name'] as String, e['count'] as int))
        .toList();
  }

  Future<List<NamedCount>> issuesByCategory() async {
    final response = await _dio.get('/analytics/issues-by-category');
    return (response.data as List)
        .map((e) => NamedCount(e['name'] as String, e['count'] as int))
        .toList();
  }

  Future<List<FieldAsset>> mapAssets({String? risk}) async {
    final response = await _dio.get('/map/assets', queryParameters: {if (risk != null) 'risk': risk});
    return (response.data as List).map((e) => FieldAsset.fromJson(Map<String, dynamic>.from(e as Map))).toList();
  }

  Future<List<AppNotification>> notifications() async {
    final response = await _dio.get('/notifications');
    return (response.data as List).map((e) => AppNotification.fromJson(Map<String, dynamic>.from(e as Map))).toList();
  }

  Future<void> markRead(String id) async {
    await _dio.post('/notifications/$id/read');
  }

  Future<Map<String, dynamic>> pushSync(String deviceId, List<Map<String, dynamic>> changes) async {
    final response = await _dio.post('/sync/push', data: {
      'device_id': deviceId,
      'platform': 'flutter',
      'changes': changes,
    });
    return Map<String, dynamic>.from(response.data as Map);
  }

  Future<Map<String, dynamic>> pullSync(String deviceId) async {
    final response = await _dio.post('/sync/pull', data: {'device_id': deviceId});
    return Map<String, dynamic>.from(response.data as Map);
  }

  String _message(DioException e) {
    final data = e.response?.data;
    if (data is Map && data['detail'] is Map) {
      return data['detail']['message']?.toString() ?? 'Request failed';
    }
    if (data is Map && data['detail'] != null) return data['detail'].toString();
    if (e.type == DioExceptionType.connectionError || e.type == DioExceptionType.connectionTimeout) {
      return 'offline';
    }
    return e.message ?? 'Request failed';
  }
}
