import 'package:fieldops_ai/core/session.dart';
import 'package:fieldops_ai/core/theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

class AppShell extends ConsumerWidget {
  const AppShell({super.key, required this.child});

  final Widget child;

  int _indexFor(String location) {
    if (location.startsWith('/map')) return 1;
    if (location.startsWith('/assets') || location.startsWith('/inspect')) return 2;
    if (location.startsWith('/work-orders')) return 3;
    if (location.startsWith('/analytics') || location.startsWith('/profile') || location.startsWith('/sync') || location.startsWith('/notifications') || location.startsWith('/inspections')) {
      return 4;
    }
    return 0;
  }

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final location = GoRouterState.of(context).uri.path;
    final session = ref.watch(sessionProvider);
    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: _indexFor(location),
        indicatorColor: FieldOpsColors.primary.withValues(alpha: 0.12),
        onDestinationSelected: (index) {
          switch (index) {
            case 0:
              context.go('/dashboard');
            case 1:
              context.go('/map');
            case 2:
              context.go('/assets');
            case 3:
              context.go('/work-orders');
            case 4:
              context.go('/profile');
          }
        },
        destinations: [
          const NavigationDestination(icon: Icon(Icons.space_dashboard_outlined), selectedIcon: Icon(Icons.space_dashboard), label: 'Home'),
          const NavigationDestination(icon: Icon(Icons.map_outlined), selectedIcon: Icon(Icons.map), label: 'Map'),
          const NavigationDestination(icon: Icon(Icons.precision_manufacturing_outlined), selectedIcon: Icon(Icons.precision_manufacturing), label: 'Assets'),
          const NavigationDestination(icon: Icon(Icons.assignment_outlined), selectedIcon: Icon(Icons.assignment), label: 'Work'),
          NavigationDestination(
            icon: Badge(
              isLabelVisible: session.pendingSync > 0 || session.notifications.any((n) => !n.read),
              child: const Icon(Icons.more_horiz),
            ),
            selectedIcon: const Icon(Icons.more_horiz),
            label: 'More',
          ),
        ],
      ),
    );
  }
}
