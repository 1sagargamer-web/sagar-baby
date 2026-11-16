import 'package:material_ui/material_ui.dart';
import 'package:shared_preferences/shared_preferences.dart';

class SettingsStore extends ChangeNotifier {
  SharedPreferences? _p;

  ThemeMode themeMode = ThemeMode.dark;
  double fontScale = 1.0; // 0.85 - 1.8
  double speed = 1.0; // 0.5 - 2.0
  int seenNoticeId = 0;
  String guestName = '';

  Future<void> load() async {
    try {
      _p = await SharedPreferences.getInstance();
      themeMode = ThemeMode.values[_p!.getInt('theme') ?? ThemeMode.dark.index];
      fontScale = _p!.getDouble('font') ?? 1.0;
      speed = _p!.getDouble('speed') ?? 1.0;
      seenNoticeId = _p!.getInt('notice') ?? 0;
      guestName = _p!.getString('guestName') ?? '';
    } catch (_) {}
    notifyListeners();
  }

  void setTheme(ThemeMode m) {
    themeMode = m;
    _p?.setInt('theme', m.index);
    notifyListeners();
  }

  void setFont(double v) {
    fontScale = v;
    _p?.setDouble('font', v);
    notifyListeners();
  }

  void setSpeed(double v) {
    speed = v;
    _p?.setDouble('speed', v);
    notifyListeners();
  }

  void markNoticeSeen(int id) {
    seenNoticeId = id;
    _p?.setInt('notice', id);
  }

  void setGuestName(String n) {
    guestName = n;
    _p?.setString('guestName', n);
    notifyListeners();
  }
}
