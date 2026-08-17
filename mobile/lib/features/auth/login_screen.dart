import 'package:fieldops_ai/core/config.dart';
import 'package:fieldops_ai/core/session.dart';
import 'package:fieldops_ai/core/theme.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class LoginScreen extends ConsumerStatefulWidget {
  const LoginScreen({super.key});

  @override
  ConsumerState<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends ConsumerState<LoginScreen> {
  final email = TextEditingController(text: AppConfig.demoEmail);
  final password = TextEditingController(text: AppConfig.demoPassword);
  final server = TextEditingController();

  @override
  void initState() {
    super.initState();
    server.text = ref.read(sessionProvider).baseUrl ?? AppConfig.defaultBaseUrl;
  }

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(sessionProvider);
    return Scaffold(
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.fromLTRB(24, 36, 24, 24),
          children: [
            const Icon(Icons.hub_outlined, size: 48, color: FieldOpsColors.primary),
            const SizedBox(height: 16),
            const Text('FieldOps AI', style: TextStyle(fontSize: 32, fontWeight: FontWeight.w800)),
            const SizedBox(height: 8),
            const Text(
              'An AI-assisted field operations intelligence platform. AI assists decisions; it does not control critical business rules.',
              style: TextStyle(color: FieldOpsColors.muted, height: 1.4),
            ),
            const SizedBox(height: 28),
            TextField(controller: email, decoration: const InputDecoration(labelText: 'Email')),
            const SizedBox(height: 12),
            TextField(controller: password, obscureText: true, decoration: const InputDecoration(labelText: 'Password')),
            const SizedBox(height: 12),
            TextField(controller: server, decoration: const InputDecoration(labelText: 'API base URL')),
            if (session.error != null) ...[
              const SizedBox(height: 12),
              Text(session.error!, style: const TextStyle(color: FieldOpsColors.critical)),
            ],
            const SizedBox(height: 20),
            FilledButton(
              onPressed: session.busy
                  ? null
                  : () async {
                      await ref.read(sessionProvider.notifier).setBaseUrl(server.text.trim());
                      await ref.read(sessionProvider.notifier).login(email.text.trim(), password.text);
                    },
              child: Text(session.busy ? 'Signing in…' : 'Sign in'),
            ),
            const SizedBox(height: 24),
            const Text('Demo accounts  ·  password Demo@12345', style: TextStyle(fontWeight: FontWeight.w700)),
            const SizedBox(height: 8),
            const Text('inspector@fieldops.ai\nsupervisor@fieldops.ai\nmanager@fieldops.ai\nadmin@fieldops.ai', style: TextStyle(color: FieldOpsColors.muted, height: 1.5)),
          ],
        ),
      ),
    );
  }
}
