import 'package:flutter/services.dart';
import 'package:just_audio_background/just_audio_background.dart';
import 'package:material_ui/material_ui.dart';
import 'package:provider/provider.dart';

import 'core/config.dart';
import 'core/theme.dart';
import 'screens/gate.dart';
import 'services/api.dart';
import 'services/backend.dart';
import 'services/extract.dart';
import 'services/library.dart';
import 'services/player.dart';
import 'services/settings.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  SystemChrome.setEnabledSystemUIMode(SystemUiMode.edgeToEdge);
  SystemChrome.setSystemUIOverlayStyle(const SystemUiOverlayStyle(
    statusBarColor: Colors.transparent,
    systemNavigationBarColor: Colors.transparent,
  ));

  // Background + lock screen pe awaaz chalti rahe
  await JustAudioBackground.init(
    androidNotificationChannelId: 'com.sagar.vaani.audio',
    androidNotificationChannelName: 'Sagar Vaani - Awaaz',
    androidNotificationOngoing: true,
    notificationColor: VColors.ocean,
    androidNotificationIcon: 'drawable/ic_stat_vaani',
  );

  final settings = SettingsStore();
  final library = LibraryStore();
  await Future.wait([settings.load(), library.load()]);

  final backend = Backend();
  final api = Api(backend);
  final player = VoicePlayer(api)..speed = settings.speed;

  runApp(MultiProvider(
    providers: [
      ChangeNotifierProvider.value(value: settings),
      ChangeNotifierProvider.value(value: library),
      ChangeNotifierProvider.value(value: backend),
      ChangeNotifierProvider.value(value: player),
      Provider.value(value: api),
      Provider.value(value: Extractor(api)),
    ],
    child: const VaaniApp(),
  ));

  backend.init();
}

class VaaniApp extends StatelessWidget {
  const VaaniApp({super.key});

  @override
  Widget build(BuildContext context) {
    final mode = context.select<SettingsStore, ThemeMode>((s) => s.themeMode);
    return MaterialApp(
      title: AppConfig.appName,
      debugShowCheckedModeBanner: false,
      theme: VTheme.build(Brightness.light),
      darkTheme: VTheme.build(Brightness.dark),
      themeMode: mode,
      home: const RootGate(),
    );
  }
}
