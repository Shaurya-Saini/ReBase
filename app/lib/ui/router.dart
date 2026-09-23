import 'package:go_router/go_router.dart';

import 'package:app/features/login/login_screen.dart';
import 'package:app/features/mode_switch/mode_switch_screen.dart';
import 'package:app/features/dashboard/dashboard_screen.dart';
import 'package:app/features/job/job_screen.dart';
import 'package:app/features/session/pre_start_screen.dart';
import 'package:app/features/session/briefing_screen.dart';
import 'package:app/features/session/live_screen.dart';
import 'package:app/features/assistant/assistant_screen.dart';
// B provides this screen (CONTRACT §6.1); the route lives here because A owns the router.
import 'package:app/features/training/training_hub_screen.dart';

/// A owns navigation (CONTRACT §6.2). B's `main.dart` calls `buildRouter()`.
GoRouter buildRouter() {
  return GoRouter(
    initialLocation: '/',
    routes: [
      GoRoute(path: '/', builder: (c, s) => const LoginScreen()),
      GoRoute(path: '/mode', builder: (c, s) => const ModeSwitchScreen()),
      GoRoute(path: '/dashboard', builder: (c, s) => const DashboardScreen()),
      GoRoute(
        path: '/job/:jobId',
        builder: (c, s) => JobScreen(jobId: s.pathParameters['jobId']!),
      ),
      GoRoute(
        path: '/session/:id/pre-start',
        builder: (c, s) => PreStartScreen(sessionId: s.pathParameters['id']!),
      ),
      GoRoute(
        path: '/session/:id/briefing',
        builder: (c, s) => BriefingScreen(sessionId: s.pathParameters['id']!),
      ),
      GoRoute(
        path: '/session/:id/live',
        builder: (c, s) => LiveScreen(sessionId: s.pathParameters['id']!),
      ),
      GoRoute(path: '/assistant', builder: (c, s) => const AssistantScreen()),
      // /training → B's screen. Args passed as query params for now (A12 will refine).
      GoRoute(
        path: '/training',
        builder: (c, s) => TrainingHubScreen(
          operatorId: s.uri.queryParameters['operatorId'] ?? '',
          machineType: s.uri.queryParameters['machineType'] ?? 'excavator',
        ),
      ),
    ],
  );
}
