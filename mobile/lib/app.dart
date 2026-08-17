import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fieldops_ai/core/router.dart';
import 'package:fieldops_ai/core/theme.dart';

class FieldOpsApp extends ConsumerWidget {
  const FieldOpsApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);
    return MaterialApp.router(
      title: 'FieldOps AI',
      debugShowCheckedModeBanner: false,
      theme: FieldOpsTheme.light(),
      routerConfig: router,
    );
  }
}
