import 'package:material_ui/material_ui.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../core/config.dart';
import '../core/theme.dart';
import '../services/backend.dart';
import '../services/player.dart';
import '../services/settings.dart';
import '../widgets/common.dart';
import '../widgets/player_bar.dart';

class SettingsScreen extends StatelessWidget {
  const SettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final s = context.watch<SettingsStore>();
    final b = context.watch<Backend>();
    final name = b.name.isNotEmpty ? b.name : (s.guestName.isNotEmpty ? s.guestName : 'Dost');

    return SafeArea(
      bottom: false,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(18, 10, 18, 190),
        children: [
          const Text('Settings', style: TextStyle(fontSize: 28, fontWeight: FontWeight.w800)),
          const SizedBox(height: 16),

          // ------------------------------------------------------------ profile
          Glass(
            child: Row(children: [
              Container(
                width: 56,
                height: 56,
                alignment: Alignment.center,
                decoration: const BoxDecoration(shape: BoxShape.circle, gradient: VColors.brand),
                child: Text(name.characters.first.toUpperCase(), style: const TextStyle(color: Colors.white, fontSize: 24, fontWeight: FontWeight.w800)),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(name, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
                  Text(b.user?.email ?? 'Guest', style: TextStyle(fontSize: 13, color: Theme.of(context).hintColor)),
                  if (b.isAdmin)
                    Container(
                      margin: const EdgeInsets.only(top: 6),
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                      decoration: BoxDecoration(gradient: VColors.warm, borderRadius: BorderRadius.circular(10)),
                      child: const Text('👑 OWNER', style: TextStyle(color: Colors.white, fontSize: 11, fontWeight: FontWeight.w800)),
                    ),
                ]),
              ),
              if (!b.firebaseOn)
                IconButton(
                  icon: const Icon(Icons.edit_rounded),
                  onPressed: () async {
                    final c = TextEditingController(text: s.guestName);
                    final n = await showDialog<String>(
                      context: context,
                      builder: (d) => AlertDialog(
                        title: const Text('Aapka naam'),
                        content: TextField(controller: c, autofocus: true),
                        actions: [FilledButton(onPressed: () => Navigator.pop(d, c.text), child: const Text('Save'))],
                      ),
                    );
                    if (n != null) s.setGuestName(n.trim());
                  },
                ),
            ]),
          ),

          // ------------------------------------------------------------ look
          const SectionTitle('Dikhawat'),
          Glass(
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Row(children: [Icon(Icons.dark_mode_rounded), SizedBox(width: 10), Text('Theme', style: TextStyle(fontWeight: FontWeight.w600))]),
              const SizedBox(height: 12),
              Row(children: [
                for (final m in [(ThemeMode.dark, '🌙 Dark'), (ThemeMode.light, '☀️ Light'), (ThemeMode.system, '📱 Auto')])
                  Expanded(
                    child: Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 4),
                      child: Pressable(
                        onTap: () => s.setTheme(m.$1),
                        child: AnimatedContainer(
                          duration: const Duration(milliseconds: 250),
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          alignment: Alignment.center,
                          decoration: BoxDecoration(
                            gradient: s.themeMode == m.$1 ? VColors.brand : null,
                            color: s.themeMode == m.$1 ? null : Theme.of(context).hintColor.withValues(alpha: 0.1),
                            borderRadius: BorderRadius.circular(16),
                          ),
                          child: Text(m.$2, style: TextStyle(fontWeight: FontWeight.w600, color: s.themeMode == m.$1 ? Colors.white : null)),
                        ),
                      ),
                    ),
                  ),
              ]),
              const SizedBox(height: 20),
              Row(children: [
                const Icon(Icons.format_size_rounded),
                const SizedBox(width: 10),
                const Text('Akshar ka size', style: TextStyle(fontWeight: FontWeight.w600)),
                const Spacer(),
                Text('${(s.fontScale * 100).round()}%', style: TextStyle(color: Theme.of(context).hintColor)),
              ]),
              Slider(value: s.fontScale, min: 0.85, max: 1.8, divisions: 19, onChanged: s.setFont),
              Text('नमस्ते! Hello! Aise dikhega text.', style: VTheme.reader(context, s.fontScale)),
            ]),
          ),

          // ------------------------------------------------------------ voice
          const SectionTitle('Awaaz'),
          Glass(
            child: Column(children: [
              Row(children: [
                const Icon(Icons.speed_rounded),
                const SizedBox(width: 10),
                const Expanded(child: Text('Default speed', style: TextStyle(fontWeight: FontWeight.w600))),
                TextButton(onPressed: () => pickSpeed(context), child: Text(speedLabel(s.speed), style: const TextStyle(fontWeight: FontWeight.w800))),
              ]),
              const Divider(height: 22),
              Row(children: [
                const Icon(Icons.record_voice_over_rounded, color: VColors.aqua),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    const Text('Sagar ki asli awaaz', style: TextStyle(fontWeight: FontWeight.w600)),
                    Text('Har page sirf Sagar ki awaaz mein padha jaata hai', style: TextStyle(fontSize: 12, color: Theme.of(context).hintColor)),
                  ]),
                ),
                const Icon(Icons.verified_rounded, color: VColors.aqua),
              ]),
              const Divider(height: 22),
              Row(children: [
                const Icon(Icons.lock_clock_rounded),
                const SizedBox(width: 10),
                Expanded(
                  child: Text('Screen lock ho ya app band - awaaz chalti rahegi. Notification se control karo.',
                      style: TextStyle(fontSize: 13, color: Theme.of(context).hintColor)),
                ),
              ]),
            ]),
          ),

          // ------------------------------------------------------------ app
          const SectionTitle('App'),
          Glass(
            padding: const EdgeInsets.symmetric(vertical: 6),
            child: Column(children: [
              ListTile(
                leading: const Icon(Icons.system_update_rounded),
                title: Text(b.updateAvailable ? 'Naya update install karo ✨' : 'Update check karo'),
                subtitle: Text('Version ${b.version} (${b.buildNumber})'),
                onTap: () async {
                  await b.refreshGithubConfig();
                  if (!context.mounted) return;
                  if (b.updateAvailable) {
                    launchUrl(Uri.parse(b.config.updateUrl), mode: LaunchMode.externalApplication);
                  } else {
                    toast(context, 'Aap latest version pe ho ✓');
                  }
                },
              ),
              if (b.firebaseOn && b.user != null)
                ListTile(
                  leading: const Icon(Icons.logout_rounded, color: VColors.coral),
                  title: const Text('Logout', style: TextStyle(color: VColors.coral)),
                  onTap: () async {
                    await context.read<VoicePlayer>().stop();
                    await b.signOut();
                  },
                ),
            ]),
          ),
          const SizedBox(height: 26),
          Center(
            child: Column(children: [
              const VaaniLogo(size: 44, spin: false),
              const SizedBox(height: 8),
              Text('${AppConfig.appName} • Made with ❤️ by Sagar', style: TextStyle(fontSize: 12, color: Theme.of(context).hintColor)),
            ]),
          ),
        ],
      ),
    );
  }
}
