import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:app/ui/theme.dart';

void main() {
  test('AppTheme.dark() builds without asserting', () {
    // Guards against the TextStyle.apply(fontSizeFactor) assertion that crashed
    // the app at startup when a text style had a null fontSize.
    expect(AppTheme.dark(), isA<ThemeData>());
  });
}
