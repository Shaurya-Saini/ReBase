import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:app/core/api/providers.dart';
import 'package:app/core/api/ws_client.dart';
import 'package:app/core/config.dart';
import 'package:app/core/models/models.dart';
import 'package:app/edge/alert_dispatch.dart';
import 'package:app/edge/telemetry_rules.dart';
import 'package:app/l10n/app_localizations.dart';
import 'package:app/ui/alert_text.dart';
import 'package:app/ui/theme.dart';
import 'package:app/ui/widgets/alert_banner.dart';
import 'package:app/ui/widgets/status_card.dart';

/// A7 — live session: telemetry gauges from the stream fed into the on-device
/// rule engine (A8); alerts post to the incident log (E18) and show as a banner.
class LiveScreen extends ConsumerStatefulWidget {
  const LiveScreen({super.key, required this.sessionId});

  final String sessionId;

  @override
  ConsumerState<LiveScreen> createState() => _LiveScreenState();
}

class _LiveScreenState extends ConsumerState<LiveScreen> {
  final TelemetryRuleEngine _rules = TelemetryRuleEngine();
  late final AlertDispatcher _dispatcher;
  final List<Alert> _active = [];
  Telemetry? _latest;

  @override
  void initState() {
    super.initState();
    _dispatcher =
        AlertDispatcher(ref.read(apiClientProvider), widget.sessionId);
  }

  void _onTelemetry(Telemetry telemetry) {
    setState(() => _latest = telemetry);
    for (final draft in _rules.evaluate(telemetry.toData())) {
      _fire(draft);
    }
  }

  Future<void> _fire(AlertDraft draft) async {
    final alert = await _dispatcher.dispatch(draft);
    if (!mounted) return;
    setState(() => _active.add(alert));
    if (alert.severity == 'critical') {
      HapticFeedback.heavyImpact();
      SystemSound.play(SystemSoundType.alert);
    } else {
      HapticFeedback.selectionClick();
    }
  }

  Future<void> _ack(Alert a) async {
    await ref.read(apiClientProvider).ackAlert(a.id);
    if (mounted) setState(() => _active.removeWhere((x) => x.id == a.id));
  }

  Future<void> _end() async {
    final summary =
        await ref.read(apiClientProvider).endSession(widget.sessionId);
    if (!mounted) return;
    await showDialog<void>(
      context: context,
      builder: (c) => AlertDialog(
        title: const Text('Session summary'),
        content: Text('Duration: ${summary.durationHours} h\n'
            'Alerts: ${summary.alertsTotal} (critical ${summary.alertsCritical})\n'
            'Idle: ${summary.idleMinutes} min'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(c), child: const Text('OK')),
        ],
      ),
    );
    if (mounted) context.go('/dashboard');
  }

  @override
  Widget build(BuildContext context) {
    final t = AppLocalizations.of(context)!;
    ref.listen(telemetryStreamProvider(widget.sessionId), (prev, next) {
      next.whenData(_onTelemetry);
    });
    final tele = _latest;

    return Scaffold(
      appBar: AppBar(
        title: Text(t.live_title),
        actions: [
          IconButton(
            icon: const Icon(Icons.chat),
            tooltip: t.assistant_title,
            onPressed: () => context.go('/assistant'),
          ),
        ],
      ),
      body: Column(
        children: [
          if (_active.isNotEmpty)
            AlertBanner(
              title: alertText(t, _active.first.type),
              message: _active.first.message,
              severity: _active.first.severity,
              onAck: () => _ack(_active.first),
            ),
          Expanded(
            child: tele == null
                ? const Center(child: CircularProgressIndicator())
                : _gauges(tele),
          ),
          if (AppConfig.useMock) _demoTriggers(),
          Padding(
            padding: const EdgeInsets.all(12),
            child: SizedBox(
              width: double.infinity,
              child: FilledButton.icon(
                onPressed: _end,
                icon: const Icon(Icons.stop),
                label: Text(t.action_end_session),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _gauges(Telemetry x) => GridView.count(
        crossAxisCount: 4,
        childAspectRatio: 1.5,
        padding: const EdgeInsets.all(8),
        children: [
          _tile('RPM', x.engineRpm.toString(), Icons.speed),
          _tile('Hyd °C', x.hydraulicTempC.toStringAsFixed(0), Icons.thermostat,
              danger: x.hydraulicTempC > TelemetryThresholds.overheatWarnC),
          _tile('Fuel %', x.fuelPct.toString(), Icons.local_gas_station),
          _tile('Load %', x.loadPct.toStringAsFixed(0), Icons.fitness_center,
              danger: x.loadPct > TelemetryThresholds.overloadWarnPct),
          _tile('km/h', x.speedKmh.toStringAsFixed(1), Icons.directions_car),
          _tile(
              'Prox m', x.proximityM.toStringAsFixed(1), Icons.social_distance,
              danger: x.proximityM < TelemetryThresholds.proximityWarnM),
          _tile('Idle s', x.idleSeconds.toString(), Icons.hourglass_empty,
              danger: x.idleSeconds > TelemetryThresholds.idleWarnSeconds),
          _tile('Belt', x.seatbelt ? 'On' : 'Off',
              Icons.airline_seat_recline_normal,
              danger: !x.seatbelt),
        ],
      );

  Widget _tile(String label, String value, IconData icon,
          {bool danger = false}) =>
      StatusCard(
        title: label,
        value: value,
        icon: icon,
        color: danger ? AppTheme.critical : null,
      );

  /// Mock-only buttons so alerts are demoable without the backend simulator.
  /// (On a real device the camera CV of A9 raises the edge_cv alerts.)
  Widget _demoTriggers() => Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8),
        child: Wrap(
          spacing: 8,
          children: [
            OutlinedButton(
                onPressed: () =>
                    _onTelemetry(_craft(seatbelt: false, speed: 5)),
                child: const Text('Seatbelt')),
            OutlinedButton(
                onPressed: () => _onTelemetry(_craft(proximity: 1.2)),
                child: const Text('Proximity')),
            OutlinedButton(
                onPressed: () => _onTelemetry(_craft(temp: 110)),
                child: const Text('Overheat')),
            OutlinedButton(
                onPressed: () => _fire(AlertDraft(
                    type: 'drowsiness',
                    source: 'edge_cv',
                    severity: 'critical',
                    message: 'Operator eyes closed for more than 2 seconds')),
                child: const Text('Drowsy (CV)')),
          ],
        ),
      );

  Telemetry _craft({
    bool seatbelt = true,
    double speed = 0,
    double proximity = 12,
    double temp = 60,
    double load = 40,
  }) =>
      Telemetry(
        ts: DateTime.now().toUtc().toIso8601String(),
        engineRpm: 1500,
        hydraulicTempC: temp,
        fuelPct: 70,
        loadPct: load,
        speedKmh: speed,
        idleSeconds: 0,
        seatbelt: seatbelt,
        proximityM: proximity,
      );
}
