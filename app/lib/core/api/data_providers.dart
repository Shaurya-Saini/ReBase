import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:app/core/api/providers.dart';
import 'package:app/core/models/models.dart';

/// All operators (login picker).
final operatorsProvider = FutureProvider.autoDispose<List<Operator>>(
    (ref) => ref.watch(apiClientProvider).operators());

/// The operator chosen at login — drives the dashboard and session flow.
final selectedOperatorProvider = StateProvider<Operator?>((ref) => null);

/// Selected assignment range on the dashboard.
final rangeProvider = StateProvider<String>((ref) => 'day');

/// Assignments for an operator + range.
final assignmentsProvider = FutureProvider.autoDispose
    .family<List<Assignment>, ({String operatorId, String range})>(
  (ref, args) => ref
      .watch(apiClientProvider)
      .assignments(args.operatorId, range: args.range),
);

/// All machines (used to resolve one of the job's type when starting a session).
final machinesProvider = FutureProvider.autoDispose<List<Machine>>(
    (ref) => ref.watch(apiClientProvider).machines());

/// One job (A4).
final jobProvider = FutureProvider.autoDispose
    .family<Job, String>((ref, id) => ref.watch(apiClientProvider).job(id));

/// XGBoost estimate for a job (A4).
final estimateProvider = FutureProvider.autoDispose.family<Estimate, String>(
    (ref, jobId) => ref.watch(apiClientProvider).estimate(jobId));

/// Pre-start checklist for a session (A5).
final checklistProvider = FutureProvider.autoDispose.family<Checklist, String>(
    (ref, sessionId) => ref.watch(apiClientProvider).checklist(sessionId));

/// Operational briefing for a session in a language (A6).
final briefingProvider = FutureProvider.autoDispose
    .family<Briefing, ({String sessionId, String lang})>((ref, a) =>
        ref.watch(apiClientProvider).briefing(a.sessionId, lang: a.lang));

/// Next pre-shift training module for an operator + machine (A18, E26).
final trainingModuleProvider = FutureProvider.autoDispose
    .family<TrainingModule, ({String operatorId, String machineType})>((ref,
            a) =>
        ref.watch(apiClientProvider).nextTraining(a.operatorId, a.machineType));
