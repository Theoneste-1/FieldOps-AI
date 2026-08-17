import 'package:fieldops_ai/core/session.dart';
import 'package:fieldops_ai/features/analytics/analytics_screen.dart';
import 'package:fieldops_ai/features/assets/asset_detail_screen.dart';
import 'package:fieldops_ai/features/assets/asset_list_screen.dart';
import 'package:fieldops_ai/features/auth/login_screen.dart';
import 'package:fieldops_ai/features/dashboard/dashboard_screen.dart';
import 'package:fieldops_ai/features/inspections/inspection_detail_screen.dart';
import 'package:fieldops_ai/features/inspections/inspection_form_screen.dart';
import 'package:fieldops_ai/features/inspections/inspection_list_screen.dart';
import 'package:fieldops_ai/features/maps/map_screen.dart';
import 'package:fieldops_ai/features/notifications/notifications_screen.dart';
import 'package:fieldops_ai/features/profile/profile_screen.dart';
import 'package:fieldops_ai/features/shell/app_shell.dart';
import 'package:fieldops_ai/features/splash/splash_screen.dart';
import 'package:fieldops_ai/features/sync/sync_screen.dart';
import 'package:fieldops_ai/features/work_orders/work_orders_screen.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

final routerProvider = Provider<GoRouter>((ref) {
  final bootstrapped = ref.watch(sessionProvider.select((s) => s.bootstrapped));
  final loggedIn = ref.watch(sessionProvider.select((s) => s.isLoggedIn));
  return GoRouter(
    initialLocation: '/splash',
    redirect: (context, state) {
      if (!bootstrapped) return '/splash';
      final loc = state.matchedLocation;
      if (!loggedIn && loc != '/login') return '/login';
      if (loggedIn && (loc == '/login' || loc == '/splash')) return '/dashboard';
      return null;
    },
    routes: [
      GoRoute(path: '/splash', builder: (context, state) => const SplashScreen()),
      GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),
      ShellRoute(
        builder: (context, state, child) => AppShell(child: child),
        routes: [
          GoRoute(path: '/dashboard', builder: (context, state) => const DashboardScreen()),
          GoRoute(path: '/map', builder: (context, state) => const MapScreen()),
          GoRoute(path: '/assets', builder: (context, state) => const AssetListScreen()),
          GoRoute(path: '/assets/:id', builder: (context, state) => AssetDetailScreen(assetId: state.pathParameters['id']!)),
          GoRoute(path: '/inspect/:assetId', builder: (context, state) => InspectionFormScreen(assetId: state.pathParameters['assetId']!)),
          GoRoute(path: '/inspections', builder: (context, state) => const InspectionListScreen()),
          GoRoute(path: '/inspections/:id', builder: (context, state) => InspectionDetailScreen(inspectionId: state.pathParameters['id']!)),
          GoRoute(path: '/work-orders', builder: (context, state) => const WorkOrdersScreen()),
          GoRoute(path: '/analytics', builder: (context, state) => const AnalyticsScreen()),
          GoRoute(path: '/notifications', builder: (context, state) => const NotificationsScreen()),
          GoRoute(path: '/profile', builder: (context, state) => const ProfileScreen()),
          GoRoute(path: '/sync', builder: (context, state) => const SyncScreen()),
        ],
      ),
    ],
  );
});
