import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class FieldOpsColors {
  static const primary = Color(0xFF0F3D3E);
  static const primarySoft = Color(0xFF1B5B5C);
  static const accent = Color(0xFFF4A261);
  static const background = Color(0xFFF4F1EC);
  static const surface = Color(0xFFFFFCF8);
  static const ink = Color(0xFF1C1917);
  static const muted = Color(0xFF6B635B);
  static const line = Color(0xFFE6DFD6);
  static const low = Color(0xFF2A9D8F);
  static const medium = Color(0xFFE9C46A);
  static const high = Color(0xFFF4A261);
  static const critical = Color(0xFFE63946);

  static Color risk(String level) {
    switch (level.toLowerCase()) {
      case 'critical':
        return critical;
      case 'high':
        return high;
      case 'medium':
        return medium;
      default:
        return low;
    }
  }
}

class FieldOpsTheme {
  static ThemeData light() {
    final base = ColorScheme.fromSeed(
      seedColor: FieldOpsColors.primary,
      primary: FieldOpsColors.primary,
      surface: FieldOpsColors.surface,
    );
    return ThemeData(
      useMaterial3: true,
      colorScheme: base,
      scaffoldBackgroundColor: FieldOpsColors.background,
      textTheme: GoogleFonts.sourceSans3TextTheme(),
      appBarTheme: AppBarTheme(
        backgroundColor: FieldOpsColors.background,
        foregroundColor: FieldOpsColors.ink,
        elevation: 0,
        centerTitle: false,
        titleTextStyle: GoogleFonts.sourceSans3(
          fontSize: 20,
          fontWeight: FontWeight.w700,
          color: FieldOpsColors.ink,
        ),
      ),
      cardTheme: CardThemeData(
        color: FieldOpsColors.surface,
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(18),
          side: const BorderSide(color: FieldOpsColors.line),
        ),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: FieldOpsColors.surface,
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(14)),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: FieldOpsColors.line),
        ),
      ),
      filledButtonTheme: FilledButtonThemeData(
        style: FilledButton.styleFrom(
          backgroundColor: FieldOpsColors.primary,
          foregroundColor: Colors.white,
          minimumSize: const Size.fromHeight(52),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
        ),
      ),
    );
  }
}
