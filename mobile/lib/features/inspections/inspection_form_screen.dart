import 'package:collection/collection.dart';
import 'package:fieldops_ai/core/models.dart';
import 'package:fieldops_ai/core/risk_engine.dart';
import 'package:fieldops_ai/core/session.dart';
import 'package:fieldops_ai/core/theme.dart';
import 'package:fieldops_ai/core/widgets.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:image_picker/image_picker.dart';

class InspectionFormScreen extends ConsumerStatefulWidget {
  const InspectionFormScreen({super.key, required this.assetId});

  final String assetId;

  @override
  ConsumerState<InspectionFormScreen> createState() => _InspectionFormScreenState();
}

class _InspectionFormScreenState extends ConsumerState<InspectionFormScreen> {
  final notes = TextEditingController(text: 'There is oil around the bottom and the machine is unusually noisy.');
  double temperature = 91;
  bool oilLeak = true;
  String noise = 'high';
  bool visualDamage = true;
  bool photoAttached = false;
  bool submitting = false;

  @override
  Widget build(BuildContext context) {
    final session = ref.watch(sessionProvider);
    final asset = session.assets.where((a) => a.id == widget.assetId).firstOrNull;
    if (asset == null) return const Scaffold(body: Center(child: Text('Asset not found')));

    final observations = [
      Observation(fieldKey: 'oil_leakage', label: 'Oil leakage', category: 'leakage', valueBool: oilLeak, valueText: oilLeak ? 'Yes' : 'No'),
      Observation(fieldKey: 'noise', label: 'Noise', category: 'noise', valueText: noise, severity: noise == 'high' ? 'high' : 'medium'),
      Observation(fieldKey: 'visual_damage', label: 'Visual damage', category: 'structural', valueBool: visualDamage, valueText: visualDamage ? 'Yes' : 'No'),
    ];
    final measurements = [
      Measurement(fieldKey: 'temperature', label: 'Operating temperature', value: temperature, unit: '°C', maxThreshold: 80, isAbnormal: temperature > 80),
    ];
    final preview = RiskEngine.calculate(observations: observations, measurements: measurements, previousFailures: asset.code == 'T-104' ? 1 : 0);

    return Scaffold(
      appBar: AppBar(title: Text('Inspect ${asset.code}')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          OfflineBanner(offline: session.offline, pending: session.pendingSync),
          Text(asset.name, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800)),
          const SizedBox(height: 16),
          Text('Temperature  ${temperature.round()}°C', style: const TextStyle(fontWeight: FontWeight.w700)),
          Slider(value: temperature, min: 40, max: 120, onChanged: (v) => setState(() => temperature = v)),
          SwitchListTile(title: const Text('Oil leakage'), value: oilLeak, onChanged: (v) => setState(() => oilLeak = v)),
          const Text('Noise', style: TextStyle(fontWeight: FontWeight.w700)),
          Wrap(
            spacing: 8,
            children: ['normal', 'elevated', 'high'].map((item) {
              return ChoiceChip(label: Text(item), selected: noise == item, onSelected: (_) => setState(() => noise = item));
            }).toList(),
          ),
          SwitchListTile(title: const Text('Visual / structural damage'), value: visualDamage, onChanged: (v) => setState(() => visualDamage = v)),
          const SizedBox(height: 8),
          TextField(controller: notes, maxLines: 3, decoration: const InputDecoration(labelText: 'Observation notes')),
          const SizedBox(height: 12),
          OutlinedButton.icon(
            onPressed: () async {
              final picker = ImagePicker();
              XFile? file;
              try {
                file = await picker.pickImage(source: ImageSource.camera);
              } catch (_) {
                file = await picker.pickImage(source: ImageSource.gallery);
              }
              file ??= await picker.pickImage(source: ImageSource.gallery);
              if (file != null) setState(() => photoAttached = true);
            },
            icon: Icon(photoAttached ? Icons.check_circle : Icons.photo_camera_outlined),
            label: Text(photoAttached ? 'Photo attached' : 'Capture photo'),
          ),
          const SizedBox(height: 16),
          Card(
            child: ListTile(
              title: const Text('Live risk preview'),
              subtitle: const Text('Calculated on-device from business rules. Gemini does not own this score.'),
              trailing: RiskBadge(level: preview.level, score: preview.score),
            ),
          ),
          const SizedBox(height: 20),
          FilledButton(
            onPressed: submitting
                ? null
                : () async {
                    setState(() => submitting = true);
                    final record = await ref.read(sessionProvider.notifier).submitInspection(
                          asset: asset,
                          observations: observations,
                          measurements: measurements,
                          notes: notes.text,
                        );
                    if (!context.mounted) return;
                    context.go('/inspections/${record.id}');
                  },
            child: Text(submitting ? 'Submitting…' : 'Calculate risk & submit'),
          ),
          const SizedBox(height: 12),
          const Text(
            'If the network is unavailable, the inspection is stored locally and synchronized later.',
            style: TextStyle(color: FieldOpsColors.muted),
          ),
        ],
      ),
    );
  }
}
