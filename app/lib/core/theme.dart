import 'package:material_ui/material_ui.dart';
import 'package:google_fonts/google_fonts.dart';

class VColors {
  static const aqua = Color(0xFF00E0C6);
  static const ocean = Color(0xFF2F7BFF);
  static const violet = Color(0xFF8B5CF6);
  static const gold = Color(0xFFFFC857);
  static const coral = Color(0xFFFF6B8B);

  static const darkBg = Color(0xFF060A18);
  static const darkSurface = Color(0xFF0E1530);
  static const lightBg = Color(0xFFF3F6FF);

  static const brand = LinearGradient(
    colors: [aqua, ocean, violet],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );
  static const warm = LinearGradient(colors: [gold, coral]);
}

class VTheme {
  static ThemeData build(Brightness b) {
    final dark = b == Brightness.dark;
    final scheme = ColorScheme.fromSeed(
      seedColor: VColors.ocean,
      brightness: b,
      primary: dark ? VColors.aqua : VColors.ocean,
      secondary: VColors.violet,
      surface: dark ? VColors.darkSurface : Colors.white,
    );
    final base = ThemeData(useMaterial3: true, colorScheme: scheme, brightness: b);
    final text = GoogleFonts.poppinsTextTheme(base.textTheme).apply(
      bodyColor: dark ? Colors.white : const Color(0xFF0B1433),
      displayColor: dark ? Colors.white : const Color(0xFF0B1433),
    );
    return base.copyWith(
      scaffoldBackgroundColor: dark ? VColors.darkBg : VColors.lightBg,
      textTheme: text,
      appBarTheme: const AppBarTheme(backgroundColor: Colors.transparent, elevation: 0, centerTitle: false),
      snackBarTheme: SnackBarThemeData(
        behavior: SnackBarBehavior.floating,
        backgroundColor: dark ? const Color(0xFF1B2550) : const Color(0xFF0B1433),
        contentTextStyle: GoogleFonts.poppins(color: Colors.white),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      ),
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: dark ? Colors.white.withValues(alpha: 0.06) : Colors.black.withValues(alpha: 0.04),
        border: OutlineInputBorder(borderRadius: BorderRadius.circular(18), borderSide: BorderSide.none),
        contentPadding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
      ),
      bottomSheetTheme: BottomSheetThemeData(
        backgroundColor: dark ? VColors.darkSurface : Colors.white,
        shape: const RoundedRectangleBorder(borderRadius: BorderRadius.vertical(top: Radius.circular(28))),
      ),
      dialogTheme: DialogThemeData(
        backgroundColor: dark ? VColors.darkSurface : Colors.white,
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(28)),
      ),
      pageTransitionsTheme: const PageTransitionsTheme(builders: {
        TargetPlatform.android: ZoomPageTransitionsBuilder(),
      }),
    );
  }

  /// Padhne wala text (Hindi + English dono ke liye sundar font)
  static TextStyle reader(BuildContext c, double scale) => GoogleFonts.mukta(
        fontSize: 19 * scale,
        height: 1.65,
        color: Theme.of(c).brightness == Brightness.dark ? const Color(0xFFE8ECFF) : const Color(0xFF111A3A),
      );
}
