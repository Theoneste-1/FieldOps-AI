import 'package:fieldops_ai/core/theme.dart';
import 'package:flutter/material.dart';

class SplashScreen extends StatelessWidget {
  const SplashScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      backgroundColor: FieldOpsColors.primary,
      body: Center(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.hub_outlined, color: Colors.white, size: 52),
            SizedBox(height: 16),
            Text('FieldOps AI', style: TextStyle(color: Colors.white, fontSize: 28, fontWeight: FontWeight.w800)),
            SizedBox(height: 8),
            Text('Field observations → operational intelligence', style: TextStyle(color: Colors.white70)),
          ],
        ),
      ),
    );
  }
}
