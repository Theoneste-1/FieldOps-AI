import 'package:flutter/foundation.dart';

class AppConfig {
  static const String compiledApiBaseUrl = String.fromEnvironment('API_BASE_URL');

  static String get defaultBaseUrl {
    if (compiledApiBaseUrl.isNotEmpty) return compiledApiBaseUrl;
    if (kIsWeb) return 'http://localhost:8000';
    if (defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:8000';
    }
    return 'http://localhost:8000';
  }

  static const demoEmail = 'inspector@fieldops.ai';
  static const demoPassword = 'Demo@12345';
}
