import 'package:fieldops_ai/core/theme.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  testWidgets('risk colors are distinct', (tester) async {
    expect(FieldOpsColors.risk('critical'), FieldOpsColors.critical);
    expect(FieldOpsColors.risk('low'), FieldOpsColors.low);
  });
}
