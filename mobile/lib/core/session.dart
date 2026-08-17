import 'dart:convert';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:fieldops_ai/core/api.dart';
import 'package:fieldops_ai/core/config.dart';
import 'package:fieldops_ai/core/demo_data.dart';
import 'package:fieldops_ai/core/models.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:uuid/uuid.dart';

class SessionState {
  SessionState({
    this.user,
    this.token,
    this.baseUrl,
    this.offline = false,
    this.busy = false,
    this.error,
    this.assets = const [],
    this.inspections = const [],
    this.workOrders = const [],
    this.notifications = const [],
    this.kpis,
    this.riskDistribution = const [],
    this.issueCategories = const [],
    this.pendingSync = 0,
    this.bootstrapped = false,
  });

  final UserAccount? user;
  final String? token;
  final String? baseUrl;
  final bool offline;
  final bool busy;
  final String? error;
  final List<FieldAsset> assets;
  final List<InspectionRecord> inspections;
  final List<WorkOrderRecord> workOrders;
  final List<AppNotification> notifications;
  final KpiSnapshot? kpis;
  final List<NamedCount> riskDistribution;
  final List<NamedCount> issueCategories;
  final int pendingSync;
  final bool bootstrapped;

  bool get isLoggedIn => user != null;

  SessionState copyWith({
    UserAccount? user,
    String? token,
    String? baseUrl,
    bool? offline,
    bool? busy,
    String? error,
    bool clearError = false,
    List<FieldAsset>? assets,
    List<InspectionRecord>? inspections,
    List<WorkOrderRecord>? workOrders,
    List<AppNotification>? notifications,
    KpiSnapshot? kpis,
    List<NamedCount>? riskDistribution,
    List<NamedCount>? issueCategories,
    int? pendingSync,
    bool? bootstrapped,
    bool clearUser = false,
  }) {
    return SessionState(
      user: clearUser ? null : user ?? this.user,
      token: clearUser ? null : token ?? this.token,
      baseUrl: baseUrl ?? this.baseUrl,
      offline: offline ?? this.offline,
      busy: busy ?? this.busy,
      error: clearError ? null : error ?? this.error,
      assets: assets ?? this.assets,
      inspections: inspections ?? this.inspections,
      workOrders: workOrders ?? this.workOrders,
      notifications: notifications ?? this.notifications,
      kpis: kpis ?? this.kpis,
      riskDistribution: riskDistribution ?? this.riskDistribution,
      issueCategories: issueCategories ?? this.issueCategories,
      pendingSync: pendingSync ?? this.pendingSync,
      bootstrapped: bootstrapped ?? this.bootstrapped,
    );
  }
}

class SessionController extends StateNotifier<SessionState> {
  SessionController() : super(SessionState(baseUrl: AppConfig.defaultBaseUrl)) {
    bootstrap();
  }

  final _storage = const FlutterSecureStorage();
  static const _deviceId = 'fieldops-demo-device';

  FieldOpsApi get _api => FieldOpsApi(baseUrl: state.baseUrl ?? AppConfig.defaultBaseUrl, token: state.token);

  Future<void> bootstrap() async {
    final prefs = await SharedPreferences.getInstance();
    final baseUrl = prefs.getString('baseUrl') ?? AppConfig.defaultBaseUrl;
    String? token;
    try {
      token = await _storage.read(key: 'access_token');
    } catch (_) {
      token = prefs.getString('access_token');
    }
    final userRaw = prefs.getString('user');
    UserAccount? user;
    if (userRaw != null) {
      user = UserAccount.fromJson(jsonDecode(userRaw) as Map<String, dynamic>);
    }
    state = state.copyWith(baseUrl: baseUrl, token: token, user: user, bootstrapped: true, pendingSync: prefs.getStringList('sync_queue')?.length ?? 0);
    if (user != null) {
      await refresh();
    }
  }

  Future<void> setBaseUrl(String url) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('baseUrl', url);
    state = state.copyWith(baseUrl: url);
  }

  Future<void> login(String email, String password) async {
    state = state.copyWith(busy: true, clearError: true);
    try {
      final result = await _api.login(email, password, _deviceId);
      final user = UserAccount.fromJson(Map<String, dynamic>.from(result['user'] as Map));
      final token = result['access_token'] as String;
      await _persist(user, token);
      state = state.copyWith(user: user, token: token, offline: false, busy: false);
      await refresh();
    } on ApiException catch (e) {
      if (e.message == 'offline' || e.message.contains('Invalid')) {
        // Offline or unreachable API: keep the product demoable.
        if (password == AppConfig.demoPassword && email.endsWith('@fieldops.ai')) {
          final user = DemoCatalog.userFor(email);
          await _persist(user, 'demo-token');
          state = state.copyWith(
            user: user,
            token: 'demo-token',
            offline: true,
            busy: false,
            assets: DemoCatalog.assets(),
            kpis: KpiSnapshot(inspectionsTotal: 428, critical: 31, openIssues: 76, resolvedRate: 82, openWorkOrders: 12, averageRisk: 41),
            riskDistribution: [NamedCount('low', 6), NamedCount('medium', 3), NamedCount('high', 2), NamedCount('critical', 1)],
            issueCategories: [NamedCount('temperature', 8), NamedCount('leakage', 4), NamedCount('noise', 5), NamedCount('structural', 3)],
            notifications: [
              AppNotification(id: 'n1', title: 'T-104 is due for inspection', body: 'Temperature trend is climbing. Complete a full transformer inspection.'),
            ],
            workOrders: [
              WorkOrderRecord(id: 'w1', title: 'Repair conservator bracket on T-108', priority: 'high', status: 'assigned', assetCode: 'T-108'),
            ],
          );
          return;
        }
      }
      state = state.copyWith(busy: false, error: e.message == 'offline' ? 'Unable to reach the server. Use demo credentials to continue offline.' : e.message);
    }
  }

  Future<void> logout() async {
    final prefs = await SharedPreferences.getInstance();
    await _storage.delete(key: 'access_token');
    await prefs.remove('user');
    state = SessionState(baseUrl: state.baseUrl, bootstrapped: true);
  }

  Future<void> refresh() async {
    if (state.offline || state.token == 'demo-token') {
      state = state.copyWith(assets: state.assets.isEmpty ? DemoCatalog.assets() : state.assets);
      return;
    }
    try {
      final connectivity = await Connectivity().checkConnectivity();
      final offline = connectivity.contains(ConnectivityResult.none);
      if (offline) {
        state = state.copyWith(offline: true, assets: state.assets.isEmpty ? DemoCatalog.assets() : state.assets);
        return;
      }
      final assets = await _api.assets();
      final inspections = await _api.inspections();
      final workOrders = await _api.workOrders();
      final notes = await _api.notifications();
      final kpis = await _api.kpis();
      final risk = await _api.riskDistribution();
      final issues = await _api.issuesByCategory();
      state = state.copyWith(
        assets: assets,
        inspections: inspections,
        workOrders: workOrders,
        notifications: notes,
        kpis: kpis,
        riskDistribution: risk,
        issueCategories: issues,
        offline: false,
      );
    } catch (_) {
      state = state.copyWith(
        offline: true,
        assets: state.assets.isEmpty ? DemoCatalog.assets() : state.assets,
        error: 'Working from cached / demo data. Your inspections remain stored on this device.',
      );
    }
  }

  Future<InspectionRecord> submitInspection({
    required FieldAsset asset,
    required List<Observation> observations,
    required List<Measurement> measurements,
    required String notes,
    String? weather,
  }) async {
    final payload = {
      'asset_id': asset.id,
      'notes': notes,
      'weather': weather ?? 'Clear',
      'latitude': asset.latitude,
      'longitude': asset.longitude,
      'local_id': const Uuid().v4(),
      'device_id': _deviceId,
      'observations': observations.map((e) => e.toJson()).toList(),
      'measurements': measurements.map((e) => e.toJson()).toList(),
    };
    if (!state.offline && state.token != null && state.token != 'demo-token') {
      try {
        final created = await _api.createInspection(payload);
        final submitted = await _api.submitInspection(created.id);
        state = state.copyWith(inspections: [submitted, ...state.inspections]);
        await refresh();
        return submitted;
      } catch (_) {
        // fall through to local save
      }
    }
    final local = DemoCatalog.wowInspection(asset, observations, measurements, notes);
    final nextAssets = [
      for (final item in state.assets)
        if (item.id == asset.id)
          FieldAsset(
            id: item.id,
            code: item.code,
            name: item.name,
            riskLevel: local.risk?.level ?? item.riskLevel,
            riskScore: local.risk?.score ?? item.riskScore,
            description: item.description,
            status: item.status,
            latitude: item.latitude,
            longitude: item.longitude,
            typeName: item.typeName,
            locationName: item.locationName,
            lastInspectionAt: DateTime.now().toIso8601String(),
          )
        else
          item,
    ];
    final prefs = await SharedPreferences.getInstance();
    final queue = prefs.getStringList('sync_queue') ?? [];
    queue.add(jsonEncode(payload));
    await prefs.setStringList('sync_queue', queue);
    state = state.copyWith(
      inspections: [local, ...state.inspections],
      assets: nextAssets,
      pendingSync: queue.length,
      kpis: KpiSnapshot(
        inspectionsTotal: (state.kpis?.inspectionsTotal ?? 427) + 1,
        critical: (state.kpis?.critical ?? 30) + ((local.risk?.level == 'critical') ? 1 : 0),
        openIssues: (state.kpis?.openIssues ?? 75) + 1,
        resolvedRate: state.kpis?.resolvedRate ?? 82,
        openWorkOrders: (state.kpis?.openWorkOrders ?? 11) + (local.risk?.level == 'critical' ? 1 : 0),
        averageRisk: local.risk?.score.toDouble() ?? 41,
      ),
      workOrders: local.risk?.level == 'critical'
          ? [
              WorkOrderRecord(
                id: const Uuid().v4(),
                title: 'Follow-up: ${asset.code} critical finding',
                priority: 'critical',
                status: 'open',
                assetCode: asset.code,
                description: 'Auto-created from a critical inspection. A supervisor must assign and approve work.',
              ),
              ...state.workOrders,
            ]
          : state.workOrders,
    );
    return local;
  }

  Future<String> syncNow() async {
    final prefs = await SharedPreferences.getInstance();
    final queue = prefs.getStringList('sync_queue') ?? [];
    if (state.offline || state.token == 'demo-token') {
      return 'Your inspection is saved locally. It will synchronize automatically when connectivity returns.';
    }
    if (queue.isEmpty) return 'Everything is already synchronized.';
    try {
      final changes = queue.map((raw) {
        final payload = jsonDecode(raw) as Map<String, dynamic>;
        return {
          'local_id': payload['local_id'],
          'entity_type': 'inspection',
          'payload': payload,
          'updated_at': DateTime.now().toUtc().toIso8601String(),
          'version': 1,
        };
      }).toList();
      await _api.pushSync(_deviceId, changes);
      await prefs.setStringList('sync_queue', []);
      state = state.copyWith(pendingSync: 0);
      await refresh();
      return 'Pending records uploaded. Server confirmation received.';
    } catch (_) {
      return 'Unable to synchronize. Your data remains safely stored on this device.';
    }
  }

  Future<void> _persist(UserAccount user, String token) async {
    final prefs = await SharedPreferences.getInstance();
    try {
      await _storage.write(key: 'access_token', value: token);
    } catch (_) {
      await prefs.setString('access_token', token);
    }
    await prefs.setString('user', jsonEncode(user.toJson()));
  }
}

final sessionProvider = StateNotifierProvider<SessionController, SessionState>((ref) => SessionController());
