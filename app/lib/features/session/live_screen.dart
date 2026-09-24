import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';

import 'package:app/core/api/providers.dart';
import 'package:app/core/api/ws_client.dart';
import 'package:app/core/config.dart';
import 'package:app/core/models/models.dart';
import 'package:app/edge/alert_dispatch.dart';
import 'package:app/edge/edge_model.dart';
import 'package:app/edge/telemetry_rules.dart';
import 'package:app/l10n/app_localizations.dart';
import 'package:app/ui/alert_text.dart';
import 'package:app/ui/theme.dart';
import 'package:app/ui/widgets/alert_banner.dart';

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
  final EdgeSafetyModel _model = EdgeSafetyModel();
  late final AlertDispatcher _dispatcher;
  final List<Alert> _active = [];
  Telemetry? _latest;

  @override
  void initState() {
    super.initState();
    _dispatcher =
        AlertDispatcher(ref.read(apiClientProvider), widget.sessionId);
    _model.load(); // uses the trained model if bundled; else rules
  }

  @override
  void dispose() {
    _model.close();
    super.dispose();
  }

  void _onTelemetry(Telemetry telemetry) {
    setState(() => _latest = telemetry);
    // Learned edge model when available, threshold rules otherwise.
    final drafts = _model.isLoaded
        ? _model.evaluate(telemetry)
        : _rules.evaluate(telemetry.toData());
    for (final draft in drafts) {
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
    final t = AppLocalizations.of(context)!;
    await showDialog<void>(
      context: context,
      builder: (c) => AlertDialog(
        title: Text(t.live_summary_title),
        content: Text('${t.live_duration}: ${summary.durationHours} h\n'
            '${t.live_alerts}: ${summary.alertsTotal} (⚠ ${summary.alertsCritical})\n'
            '${t.live_idle}: ${summary.idleMinutes} min'),
        actions: [
          TextButton(
              onPressed: () => Navigator.pop(c), child: Text(t.common_ok)),
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
            onPressed: () => context.push('/assistant'),
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
          _demoTriggers(),
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

  Widget _gauges(Telemetry x) {
    final t = AppLocalizations.of(context)!;
    return GridView.count(
      crossAxisCount: 4,
      childAspectRatio: 1.1,
      padding: const EdgeInsets.all(8),
      children: [
        _tile(t.gauge_rpm, x.engineRpm.toString(), Icons.speed),
        _tile(
            t.gauge_temp, x.hydraulicTempC.toStringAsFixed(0), Icons.thermostat,
            danger: x.hydraulicTempC > TelemetryThresholds.overheatWarnC),
        _tile(t.gauge_fuel, x.fuelPct.toString(), Icons.local_gas_station),
        _tile(t.gauge_load, x.loadPct.toStringAsFixed(0), Icons.fitness_center,
            danger: x.loadPct > TelemetryThresholds.overloadWarnPct),
        _tile(
            t.gauge_speed, x.speedKmh.toStringAsFixed(1), Icons.directions_car),
        _tile(t.gauge_proximity, x.proximityM.toStringAsFixed(1),
            Icons.social_distance,
            danger: x.proximityM < TelemetryThresholds.proximityWarnM),
        _tile(t.gauge_idle, x.idleSeconds.toString(), Icons.hourglass_empty,
            danger: x.idleSeconds > TelemetryThresholds.idleWarnSeconds),
        _tile(t.gauge_seatbelt, x.seatbelt ? t.common_on : t.common_off,
            Icons.airline_seat_recline_normal,
            danger: !x.seatbelt),
      ],
    );
  }

  Widget _tile(String label, String value, IconData icon,
      {bool danger = false}) {
    final color = danger ? AppTheme.critical : null;
    return Card(
      margin: const EdgeInsets.all(4),
      child: Padding(
        padding: const EdgeInsets.all(6),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 18, color: color),
            const SizedBox(height: 2),
            FittedBox(
              fit: BoxFit.scaleDown,
              child: Text(value,
                  style: TextStyle(
                      fontSize: 16, fontWeight: FontWeight.bold, color: color)),
            ),
            Text(label,
                style: const TextStyle(fontSize: 10),
                maxLines: 1,
                overflow: TextOverflow.ellipsis),
          ],
        ),
      ),
    );
  }

  /// Demo controls. Mock mode injects crafted telemetry locally; real mode
  /// steers the backend simulator (E22) so the actual telemetry stream changes
  /// and the on-device rules fire. The camera CV trigger stays local (the real
  /// camera raises edge_cv alerts on device — A9).
  void _demo(String event, Telemetry crafted) {
    if (AppConfig.useMock) {
      _onTelemetry(crafted);
    } else {
      ref.read(apiClientProvider).triggerScenario(widget.sessionId, event);
    }
  }

  Widget _demoTriggers() => Padding(
        padding: const EdgeInsets.symmetric(horizontal: 8),
        child: Wrap(
          spacing: 8,
          children: [
            OutlinedButton(
                onPressed: () =>
                    _demo('seatbelt_off', _craft(seatbelt: false, speed: 5)),
                child: const Text('Seatbelt')),
            OutlinedButton(
                onPressed: () => _demo('proximity', _craft(proximity: 1.2)),
                child: const Text('Proximity')),
            OutlinedButton(
                onPressed: () => _demo('overheat', _craft(temp: 110)),
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
