import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// Currently selected UI locale. A12 language switching updates this to switch
/// the whole app between en / hi / ta at runtime.
final localeProvider = StateProvider<Locale>((ref) => const Locale('en'));
