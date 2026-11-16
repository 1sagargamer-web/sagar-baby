import 'package:flutter_animate/flutter_animate.dart';
import 'package:material_ui/material_ui.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../core/config.dart';
import '../core/theme.dart';
import '../services/backend.dart';
import '../services/library.dart';
import '../services/settings.dart';
import '../widgets/common.dart';
import '../widgets/player_bar.dart';
import 'admin_screen.dart';
import 'library_screen.dart';
import 'reader_screen.dart';
import 'settings_screen.dart';
import 'sources.dart';

class HomeShell extends StatefulWidget {
  const HomeShell({super.key});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _tab = 0;
  bool _noticeOpen = false;
  late final Backend _backend = context.read<Backend>();

  @override
  void initState() {
    super.initState();
    _backend.addListener(_checkNotice);
    WidgetsBinding.instance.addPostFrameCallback((_) => _checkNotice());
  }

  @override
  void dispose() {
    _backend.removeListener(_checkNotice);
    super.dispose();
  }

  /// Owner ka naya notice aate hi popup.
  void _checkNotice() {
    if (!mounted || _noticeOpen) return;
    final c = context.read<Backend>().config;
    final s = context.read<SettingsStore>();
    if (c.noticeShow && c.noticeId > s.seenNoticeId && (c.noticeTitle.isNotEmpty || c.noticeBody.isNotEmpty)) {
      _noticeOpen = true;
      s.markNoticeSeen(c.noticeId);
      showGeneralDialog(
        context: context,
        barrierDismissible: true,
        barrierLabel: 'notice',
        transitionDuration: const Duration(milliseconds: 400),
        pageBuilder: (c2, _, __) => _NoticeDialog(title: c.noticeTitle, body: c.noticeBody),
        transitionBuilder: (_, a, __, child) => ScaleTransition(
          scale: CurvedAnimation(parent: a, curve: Curves.easeOutBack),
          child: FadeTransition(opacity: a, child: child),
        ),
      ).then((_) => _noticeOpen = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final admin = context.select<Backend, bool>((b) => b.isAdmin);
    final pages = [
      const HomeScreen(),
      const LibraryScreen(),
      const SettingsScreen(),
      if (admin) const AdminScreen(),
    ];
    final items = [
      (Icons.home_rounded, 'Home'),
      (Icons.collections_bookmark_rounded, 'Library'),
      (Icons.tune_rounded, 'Settings'),
      if (admin) (Icons.admin_panel_settings_rounded, 'Owner'),
    ];
    if (_tab >= pages.length) _tab = 0;

    return Scaffold(
      extendBody: true,
      body: OceanBackground(
        child: AnimatedSwitcher(
          duration: const Duration(milliseconds: 300),
          transitionBuilder: (c, a) => FadeTransition(opacity: a, child: SlideTransition(position: Tween(begin: const Offset(0, 0.02), end: Offset.zero).animate(a), child: c)),
          child: KeyedSubtree(key: ValueKey(_tab), child: pages[_tab]),
        ),
      ),
      bottomNavigationBar: SafeArea(
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          const MiniPlayer(),
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 10),
            child: Glass(
              radius: 28,
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 8),
              child: Row(children: [
                for (var i = 0; i < items.length; i++)
                  Expanded(
                    child: Pressable(
                      onTap: () => setState(() => _tab = i),
                      child: AnimatedContainer(
                        duration: const Duration(milliseconds: 300),
                        curve: Curves.easeOutCubic,
                        padding: const EdgeInsets.symmetric(vertical: 10),
                        decoration: BoxDecoration(
                          gradient: _tab == i ? VColors.brand : null,
                          borderRadius: BorderRadius.circular(20),
                        ),
                        child: Column(mainAxisSize: MainAxisSize.min, children: [
                          Icon(items[i].$1, color: _tab == i ? Colors.white : Theme.of(context).hintColor),
                          const SizedBox(height: 2),
                          Text(items[i].$2,
                              style: TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.w600,
                                color: _tab == i ? Colors.white : Theme.of(context).hintColor,
                              )),
                        ]),
                      ),
                    ),
                  ),
              ]),
            ),
          ),
        ]),
      ),
    );
  }
}

class _NoticeDialog extends StatelessWidget {
  const _NoticeDialog({required this.title, required this.body});
  final String title, body;

  @override
  Widget build(BuildContext context) => Center(
        child: Padding(
          padding: const EdgeInsets.all(26),
          child: Material(
            type: MaterialType.transparency,
            child: Glass(
              padding: const EdgeInsets.all(24),
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                IconBubble(icon: Icons.campaign_rounded, size: 64, gradient: VColors.warm)
                    .animate(onPlay: (c) => c.repeat(reverse: true))
                    .rotate(begin: -0.03, end: 0.03, duration: 700.ms),
                const SizedBox(height: 18),
                Text(title.isEmpty ? 'Notice' : title, textAlign: TextAlign.center, style: const TextStyle(fontSize: 21, fontWeight: FontWeight.w800)),
                const SizedBox(height: 10),
                Text(body, textAlign: TextAlign.center, style: const TextStyle(fontSize: 15, height: 1.5)),
                const SizedBox(height: 22),
                GradientButton(label: 'Theek hai 👍', onTap: () => Navigator.pop(context), height: 50),
              ]),
            ),
          ),
        ),
      );
}

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  String _greet() {
    final h = DateTime.now().hour;
    if (h < 12) return 'Suprabhat';
    if (h < 17) return 'Namaste';
    return 'Shubh sandhya';
  }

  @override
  Widget build(BuildContext context) {
    final b = context.watch<Backend>();
    final s = context.watch<SettingsStore>();
    final lib = context.watch<LibraryStore>();
    final name = b.name.isNotEmpty ? b.name : (s.guestName.isNotEmpty ? s.guestName : 'Dost');
    final recent = lib.all.take(4).toList();
    final c = b.config;

    return SafeArea(
      bottom: false,
      child: ListView(
        padding: const EdgeInsets.fromLTRB(18, 10, 18, 190),
        children: [
          // ----------------------------------------------------------- header
          Row(children: [
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text('${_greet()}, ${name.split(' ').first} 👋', style: TextStyle(fontSize: 15, color: Theme.of(context).hintColor)),
                const SizedBox(height: 2),
                GradientText(AppConfig.appName, style: const TextStyle(fontSize: 30, fontWeight: FontWeight.w800, letterSpacing: -0.5)),
              ]),
            ),
            const VaaniLogo(size: 52),
          ]).animate().fadeIn(duration: 400.ms).slideY(begin: -0.2),

          // ----------------------------------------------------------- update + notice banners
          if (b.updateAvailable)
            Padding(
              padding: const EdgeInsets.only(top: 16),
              child: Glass(
                onTap: () => launchUrl(Uri.parse(c.updateUrl), mode: LaunchMode.externalApplication),
                padding: const EdgeInsets.all(14),
                child: Row(children: [
                  const IconBubble(icon: Icons.system_update_rounded, size: 42, gradient: VColors.warm),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      const Text('Naya update aaya hai ✨', style: TextStyle(fontWeight: FontWeight.w700)),
                      Text(c.updateNote.isEmpty ? 'Tap karke update karo' : c.updateNote,
                          maxLines: 2, overflow: TextOverflow.ellipsis, style: TextStyle(fontSize: 12.5, color: Theme.of(context).hintColor)),
                    ]),
                  ),
                  const Icon(Icons.chevron_right_rounded),
                ]),
              ).animate().fadeIn().shimmer(delay: 600.ms, duration: 1200.ms),
            ),
          if (c.noticeShow && (c.noticeTitle.isNotEmpty || c.noticeBody.isNotEmpty))
            Padding(
              padding: const EdgeInsets.only(top: 12),
              child: Glass(
                padding: const EdgeInsets.all(14),
                child: Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  const Icon(Icons.campaign_rounded, color: VColors.gold),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      if (c.noticeTitle.isNotEmpty) Text(c.noticeTitle, style: const TextStyle(fontWeight: FontWeight.w700)),
                      if (c.noticeBody.isNotEmpty) Text(c.noticeBody, style: TextStyle(fontSize: 13, color: Theme.of(context).hintColor)),
                    ]),
                  ),
                ]),
              ),
            ),

          // ----------------------------------------------------------- hero: camera scan
          const SizedBox(height: 18),
          Pressable(
            onTap: () => Sources.camera(context),
            child: Container(
              padding: const EdgeInsets.all(22),
              decoration: BoxDecoration(
                gradient: VColors.brand,
                borderRadius: BorderRadius.circular(30),
                boxShadow: [BoxShadow(color: VColors.ocean.withValues(alpha: 0.45), blurRadius: 30, offset: const Offset(0, 14))],
              ),
              child: Row(children: [
                Expanded(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    const Text('Page Scan karo', style: TextStyle(color: Colors.white, fontSize: 22, fontWeight: FontWeight.w800)),
                    const SizedBox(height: 6),
                    Text('Camera se photo lo - main Sagar ki awaaz mein padh ke sunaunga',
                        style: TextStyle(color: Colors.white.withValues(alpha: 0.9), fontSize: 13.5, height: 1.4)),
                    const SizedBox(height: 16),
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                      decoration: BoxDecoration(color: Colors.white, borderRadius: BorderRadius.circular(20)),
                      child: const Row(mainAxisSize: MainAxisSize.min, children: [
                        Icon(Icons.document_scanner_rounded, color: VColors.ocean, size: 20),
                        SizedBox(width: 8),
                        Text('Camera kholo', style: TextStyle(color: VColors.ocean, fontWeight: FontWeight.w700)),
                      ]),
                    ),
                  ]),
                ),
                const SizedBox(width: 10),
                Icon(Icons.photo_camera_rounded, color: Colors.white, size: 74)
                    .animate(onPlay: (c) => c.repeat(reverse: true))
                    .scale(begin: const Offset(0.92, 0.92), end: const Offset(1.05, 1.05), duration: 1600.ms, curve: Curves.easeInOut),
              ]),
            ),
          ).animate(delay: 100.ms).fadeIn(duration: 500.ms).slideY(begin: 0.15, curve: Curves.easeOutCubic),

          // ----------------------------------------------------------- other sources
          const SectionTitle('Ya yahan se laao'),
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            mainAxisSpacing: 14,
            crossAxisSpacing: 14,
            childAspectRatio: 1.35,
            children: [
              _SourceTile(icon: Icons.photo_library_rounded, title: 'Photo', sub: 'Gallery se, ek ya kai', gradient: const LinearGradient(colors: [Color(0xFF00E0C6), Color(0xFF00A3FF)]), onTap: () => Sources.photos(context)),
              _SourceTile(icon: Icons.picture_as_pdf_rounded, title: 'PDF', sub: 'Book, notes, file', gradient: const LinearGradient(colors: [Color(0xFFFF6B8B), Color(0xFFFF8E53)]), onTap: () => Sources.pdf(context)),
              _SourceTile(icon: Icons.edit_note_rounded, title: 'Text', sub: 'Likho ya paste karo', gradient: const LinearGradient(colors: [Color(0xFF8B5CF6), Color(0xFF6366F1)]), onTap: () => Sources.text(context)),
              _SourceTile(icon: Icons.language_rounded, title: 'Web Page', sub: 'Kisi bhi site ka link', gradient: const LinearGradient(colors: [Color(0xFFFFC857), Color(0xFFFF9F43)]), onTap: () => Sources.link(context)),
            ].animate(interval: 70.ms).fadeIn(duration: 400.ms).scale(begin: const Offset(0.9, 0.9), curve: Curves.easeOutBack),
          ),

          // ----------------------------------------------------------- recent
          if (recent.isNotEmpty) ...[
            const SectionTitle('Haal hi mein padha'),
            for (final d in recent) DocTile(doc: d),
          ] else ...[
            const SizedBox(height: 26),
            Glass(
              child: Row(children: [
                const Icon(Icons.tips_and_updates_rounded, color: VColors.gold),
                const SizedBox(width: 12),
                Expanded(
                  child: Text('Tip: Page khulne ke baad koi bhi line select karo aur "Sunao" dabao - sirf utna hi padhunga.',
                      style: TextStyle(fontSize: 13.5, color: Theme.of(context).hintColor, height: 1.4)),
                ),
              ]),
            ),
          ],
        ],
      ),
    );
  }
}

class _SourceTile extends StatelessWidget {
  const _SourceTile({required this.icon, required this.title, required this.sub, required this.gradient, required this.onTap});
  final IconData icon;
  final String title, sub;
  final Gradient gradient;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Glass(
        onTap: onTap,
        padding: const EdgeInsets.all(16),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          IconBubble(icon: icon, gradient: gradient, size: 44),
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(title, style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
            Text(sub, maxLines: 1, overflow: TextOverflow.ellipsis, style: TextStyle(fontSize: 12, color: Theme.of(context).hintColor)),
          ]),
        ]),
      );
}

IconData sourceIcon(String s) => switch (s) {
      'camera' => Icons.document_scanner_rounded,
      'photo' => Icons.photo_rounded,
      'pdf' => Icons.picture_as_pdf_rounded,
      'link' => Icons.language_rounded,
      _ => Icons.notes_rounded,
    };

String ago(DateTime t) {
  final d = DateTime.now().difference(t);
  if (d.inMinutes < 1) return 'abhi';
  if (d.inMinutes < 60) return '${d.inMinutes} min pehle';
  if (d.inHours < 24) return '${d.inHours} ghante pehle';
  if (d.inDays < 7) return '${d.inDays} din pehle';
  return '${t.day}/${t.month}/${t.year}';
}

class DocTile extends StatelessWidget {
  const DocTile({super.key, required this.doc});
  final VaaniDoc doc;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 10),
        child: Glass(
          radius: 22,
          padding: const EdgeInsets.all(14),
          onTap: () => Navigator.push(context, MaterialPageRoute(builder: (_) => ReaderScreen(doc: doc))),
          child: Row(children: [
            IconBubble(icon: sourceIcon(doc.source), size: 44),
            const SizedBox(width: 14),
            Expanded(
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(doc.title, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w600)),
                const SizedBox(height: 2),
                Text('${doc.words} shabd • ${ago(doc.openedAt)}', style: TextStyle(fontSize: 12, color: Theme.of(context).hintColor)),
              ]),
            ),
            if (doc.bookmarked) const Icon(Icons.bookmark_rounded, color: VColors.gold, size: 20),
            const Icon(Icons.play_circle_fill_rounded, color: VColors.aqua, size: 30),
          ]),
        ),
      );
}
