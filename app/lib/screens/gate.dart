import 'dart:async';

import 'package:flutter_animate/flutter_animate.dart';
import 'package:material_ui/material_ui.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../core/config.dart';
import '../services/backend.dart';
import '../widgets/common.dart';
import 'auth_screen.dart';
import 'home_shell.dart';

/// App kholte hi decide karta hai kya dikhana hai:
/// Splash -> Maintenance / Force update / Login / Block -> Home
class RootGate extends StatefulWidget {
  const RootGate({super.key});

  @override
  State<RootGate> createState() => _RootGateState();
}

class _RootGateState extends State<RootGate> with WidgetsBindingObserver {
  bool _splashDone = false;
  Timer? _poll;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    Future.delayed(const Duration(milliseconds: 1900), () {
      if (mounted) setState(() => _splashDone = true);
    });
    // Firebase na ho to har 5 minute GitHub config check
    _poll = Timer.periodic(const Duration(minutes: 5), (_) => context.read<Backend>().refreshGithubConfig());
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState s) {
    if (s == AppLifecycleState.resumed) context.read<Backend>().refreshGithubConfig();
  }

  @override
  void dispose() {
    _poll?.cancel();
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final b = context.watch<Backend>();
    Widget page;
    String key;
    if (!b.ready || !_splashDone) {
      page = const SplashScreen();
      key = 'splash';
    } else if (b.config.maintenance && !b.isAdmin) {
      page = StatusScreen.maintenance(b.config);
      key = 'maint';
    } else if (b.forceUpdate) {
      page = StatusScreen.update(b.config);
      key = 'update';
    } else if (b.needsLogin) {
      page = const AuthScreen();
      key = 'auth';
    } else if (b.blocked) {
      page = StatusScreen.blocked(onLogout: b.signOut);
      key = 'blocked';
    } else {
      page = const HomeShell();
      key = 'home';
    }
    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 600),
      switchInCurve: Curves.easeOutCubic,
      transitionBuilder: (c, a) => FadeTransition(
        opacity: a,
        child: ScaleTransition(scale: Tween(begin: 1.04, end: 1.0).animate(a), child: c),
      ),
      child: KeyedSubtree(key: ValueKey(key), child: page),
    );
  }
}

class SplashScreen extends StatelessWidget {
  const SplashScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: OceanBackground(
        child: Center(
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            VaaniLogo(size: 130)
                .animate()
                .scale(begin: const Offset(0.4, 0.4), duration: 800.ms, curve: Curves.easeOutBack)
                .fadeIn(duration: 500.ms),
            const SizedBox(height: 34),
            GradientText(AppConfig.appName, style: const TextStyle(fontSize: 38, fontWeight: FontWeight.w800, letterSpacing: -0.5))
                .animate(delay: 300.ms)
                .fadeIn(duration: 600.ms)
                .slideY(begin: 0.4, curve: Curves.easeOutCubic),
            const SizedBox(height: 8),
            Text(AppConfig.tagline, style: TextStyle(fontSize: 15, color: Theme.of(context).hintColor))
                .animate(delay: 650.ms)
                .fadeIn(duration: 600.ms),
          ]),
        ),
      ),
    );
  }
}

/// Maintenance / Update / Block screen - ek hi sundar design.
class StatusScreen extends StatelessWidget {
  const StatusScreen({
    super.key,
    required this.icon,
    required this.title,
    required this.message,
    this.buttonLabel,
    this.onButton,
  });

  final IconData icon;
  final String title, message;
  final String? buttonLabel;
  final VoidCallback? onButton;

  factory StatusScreen.maintenance(RemoteConfig c) => StatusScreen(
        icon: Icons.construction_rounded,
        title: c.maintenanceTitle.isEmpty ? 'Thoda sa kaam chal raha hai' : c.maintenanceTitle,
        message: c.maintenanceMessage.isEmpty
            ? 'App ko aur behtar banaya ja raha hai. Thodi der mein wapas aaiye 🙏'
            : c.maintenanceMessage,
      );

  factory StatusScreen.update(RemoteConfig c) => StatusScreen(
        icon: Icons.system_update_rounded,
        title: 'Naya update aa gaya hai!',
        message: c.updateNote.isEmpty ? 'App chalane ke liye naya version install karein.' : c.updateNote,
        buttonLabel: 'Abhi Update karo',
        onButton: () => launchUrl(Uri.parse(c.updateUrl), mode: LaunchMode.externalApplication),
      );

  factory StatusScreen.blocked({required Future<void> Function() onLogout}) => StatusScreen(
        icon: Icons.block_rounded,
        title: 'Account band hai',
        message: 'Aapka account owner ne rok diya hai. Kisi sawaal ke liye owner se baat karein.',
        buttonLabel: 'Logout',
        onButton: onLogout,
      );

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: OceanBackground(
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(28),
            child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
              IconBubble(icon: icon, size: 96)
                  .animate(onPlay: (c) => c.repeat(reverse: true))
                  .moveY(begin: -6, end: 6, duration: 1800.ms, curve: Curves.easeInOut),
              const SizedBox(height: 36),
              Text(title, textAlign: TextAlign.center, style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w800))
                  .animate()
                  .fadeIn()
                  .slideY(begin: 0.3),
              const SizedBox(height: 14),
              Text(message, textAlign: TextAlign.center, style: TextStyle(fontSize: 16, height: 1.5, color: Theme.of(context).hintColor))
                  .animate(delay: 150.ms)
                  .fadeIn(),
              const SizedBox(height: 40),
              if (buttonLabel != null) GradientButton(label: buttonLabel!, onTap: onButton).animate(delay: 300.ms).fadeIn().scale(),
            ]),
          ),
        ),
      ),
    );
  }
}
