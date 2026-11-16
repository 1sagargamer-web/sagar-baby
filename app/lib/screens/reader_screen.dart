import 'dart:io';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:material_ui/material_ui.dart';
import 'package:provider/provider.dart';
import 'package:share_plus/share_plus.dart';

import '../core/theme.dart';
import '../services/api.dart';
import '../services/backend.dart';
import '../services/library.dart';
import '../services/player.dart';
import '../services/settings.dart';
import '../widgets/common.dart';
import '../widgets/player_bar.dart';
import 'ask_screen.dart';

enum ViewMode { original, translation, summary }

bool isHindi(String t) {
  final dev = RegExp(r'[ऀ-ॿ]').allMatches(t).length;
  final lat = RegExp(r'[A-Za-z]').allMatches(t).length;
  return dev > lat;
}

class ReaderScreen extends StatefulWidget {
  const ReaderScreen({super.key, required this.doc, this.autoPlay = false});
  final VaaniDoc doc;
  final bool autoPlay;

  @override
  State<ReaderScreen> createState() => _ReaderScreenState();
}

class _ReaderScreenState extends State<ReaderScreen> {
  ViewMode _mode = ViewMode.original;
  String _selected = '';
  String? _spoken;
  bool _working = false;

  VaaniDoc get doc => widget.doc;

  String get _viewText => switch (_mode) {
        ViewMode.original => doc.text,
        ViewMode.translation => doc.translation ?? '',
        ViewMode.summary => doc.summary ?? '',
      };

  @override
  void initState() {
    super.initState();
    context.read<LibraryStore>().touch(doc);
    if (widget.autoPlay) WidgetsBinding.instance.addPostFrameCallback((_) => _speak(doc.text));
  }

  void _speak(String text, {String? label}) {
    final t = text.trim();
    if (t.isEmpty) return;
    _spoken = t;
    context.read<VoicePlayer>().speak(t, title: label ?? doc.title);
    context.read<Backend>().log(label == null ? 'read_page' : 'read_selected', doc.title);
    setState(() {});
  }

  bool _isMine(VoicePlayer p) => p.hasContent && (p.currentText == _spoken || p.currentText == _viewText.trim());

  void _onPlay() {
    final p = context.read<VoicePlayer>();
    if (_isMine(p)) {
      p.toggle();
    } else {
      _speak(_viewText);
    }
  }

  Future<void> _summary() async {
    if (doc.summary != null) {
      setState(() => _mode = ViewMode.summary);
      return _speak(doc.summary!, label: 'Saar • ${doc.title}');
    }
    await _ai('summary', 'Chhota saar bana raha hoon…', (r) {
      doc.summary = r;
      _mode = ViewMode.summary;
    });
    if (doc.summary != null) _speak(doc.summary!, label: 'Saar • ${doc.title}');
  }

  Future<void> _translate() async {
    final toHindi = !isHindi(doc.text);
    final choice = await showModalBottomSheet<String>(
      context: context,
      builder: (c) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(22),
          child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            const Text('Kis bhasha mein sunna hai?', style: TextStyle(fontSize: 19, fontWeight: FontWeight.w700)),
            const SizedBox(height: 18),
            GradientButton(label: 'हिंदी में  (Hindi)', icon: Icons.translate_rounded, onTap: () => Navigator.pop(c, 'hi'),
                gradient: toHindi ? VColors.brand : const LinearGradient(colors: [Color(0xFF5A6488), Color(0xFF3B4466)])),
            const SizedBox(height: 12),
            GradientButton(label: 'English mein', icon: Icons.translate_rounded, onTap: () => Navigator.pop(c, 'en'),
                gradient: !toHindi ? VColors.brand : const LinearGradient(colors: [Color(0xFF5A6488), Color(0xFF3B4466)])),
          ]),
        ),
      ),
    );
    if (choice == null) return;
    await _ai('translate', choice == 'hi' ? 'Hindi mein badal raha hoon…' : 'English mein badal raha hoon…', (r) {
      doc.translation = r;
      _mode = ViewMode.translation;
    }, target: choice);
    if (doc.translation != null && _mode == ViewMode.translation) _speak(doc.translation!, label: 'Anuvaad • ${doc.title}');
  }

  Future<void> _ai(String action, String msg, void Function(String) onDone, {String? target}) async {
    if (_working) return;
    final api = context.read<Api>();
    setState(() => _working = true);
    try {
      final r = await runWithLoader(context, msg, () => api.ai(action, doc.text, targetLang: target));
      if (r != null && r.trim().isNotEmpty) {
        onDone(r.trim());
        if (mounted) context.read<LibraryStore>().update(doc);
        if (mounted) context.read<Backend>().log(action, doc.title);
      }
    } catch (e) {
      if (mounted) toast(context, e is ApiException ? e.message : 'AI se jawab nahi aaya');
    } finally {
      if (mounted) setState(() => _working = false);
    }
  }

  Future<void> _download() async {
    final text = _selected.trim().isNotEmpty ? _selected : _viewText;
    if (text.trim().isEmpty) return;
    final player = context.read<VoicePlayer>();
    final progress = ValueNotifier<double>(0);
    File? file;
    try {
      file = await runWithLoader(
        context,
        'MP3 bana raha hoon…\nLamba page ho to thoda time lagega',
        () => player.exportMp3(text, doc.title, onProgress: (v) => progress.value = v),
      );
    } catch (e) {
      if (mounted) toast(context, e is ApiException ? e.message : 'MP3 nahi ban payi');
      return;
    }
    if (file == null || !mounted) return;
    context.read<Backend>().log('download_mp3', doc.title);
    final f = file;
    final name = f.uri.pathSegments.last;
    await showModalBottomSheet(
      context: context,
      builder: (c) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(22),
          child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Row(children: [
              const IconBubble(icon: Icons.audio_file_rounded, size: 46),
              const SizedBox(width: 14),
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  const Text('MP3 taiyaar hai! 🎉', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
                  Text(name, maxLines: 1, overflow: TextOverflow.ellipsis, style: TextStyle(color: Theme.of(c).hintColor, fontSize: 12)),
                ]),
              ),
            ]),
            const SizedBox(height: 22),
            GradientButton(
              label: 'WhatsApp / Share karo',
              icon: Icons.share_rounded,
              gradient: const LinearGradient(colors: [Color(0xFF25D366), Color(0xFF128C7E)]),
              onTap: () {
                Navigator.pop(c);
                SharePlus.instance.share(ShareParams(files: [XFile(f.path, mimeType: 'audio/mpeg')], text: '${doc.title} - Sagar Vaani'));
              },
            ),
            const SizedBox(height: 12),
            GradientButton(
              label: 'Phone mein Save karo',
              icon: Icons.save_alt_rounded,
              onTap: () async {
                Navigator.pop(c);
                final saved = await FilePicker.saveFile(fileName: name, bytes: await f.readAsBytes(), mimeType: 'audio/mpeg');
                if (mounted && saved != null) toast(context, 'Save ho gaya ✓');
              },
            ),
          ]),
        ),
      ),
    );
  }

  Future<void> _rename() async {
    final c = TextEditingController(text: doc.title);
    final t = await showDialog<String>(
      context: context,
      builder: (d) => AlertDialog(
        title: const Text('Naam badlo'),
        content: TextField(controller: c, autofocus: true),
        actions: [
          TextButton(onPressed: () => Navigator.pop(d), child: const Text('Cancel')),
          FilledButton(onPressed: () => Navigator.pop(d, c.text), child: const Text('Save')),
        ],
      ),
    );
    if (t != null && t.trim().isNotEmpty && mounted) {
      setState(() => doc.title = t.trim());
      context.read<LibraryStore>().update(doc);
    }
  }

  void _fontSheet() {
    showModalBottomSheet(
      context: context,
      builder: (c) => Consumer<SettingsStore>(
        builder: (_, s, __) => SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(22),
            child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('Akshar ka size', style: TextStyle(fontSize: 19, fontWeight: FontWeight.w700)),
              const SizedBox(height: 10),
              Row(children: [
                const Text('A', style: TextStyle(fontSize: 14)),
                Expanded(child: Slider(value: s.fontScale, min: 0.85, max: 1.8, divisions: 19, onChanged: s.setFont)),
                const Text('A', style: TextStyle(fontSize: 28, fontWeight: FontWeight.w700)),
              ]),
              Text('नमस्ते! Ye text aise dikhega.', style: VTheme.reader(c, s.fontScale)),
            ]),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final lib = context.watch<LibraryStore>();
    final scale = context.select<SettingsStore, double>((s) => s.fontScale);
    final modes = [
      ViewMode.original,
      if (doc.translation != null) ViewMode.translation,
      if (doc.summary != null) ViewMode.summary,
    ];

    return Scaffold(
      body: OceanBackground(
        child: SafeArea(
          bottom: false,
          child: Column(children: [
            // ---------------------------------------------------------------- top bar
            Padding(
              padding: const EdgeInsets.fromLTRB(6, 4, 6, 0),
              child: Row(children: [
                IconButton(onPressed: () => Navigator.pop(context), icon: const Icon(Icons.arrow_back_ios_new_rounded)),
                Expanded(
                  child: GestureDetector(
                    onTap: _rename,
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                      Text(doc.title, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
                      Text('${doc.words} shabd • ~${(doc.words / 130).ceil()} min sunne mein',
                          style: TextStyle(fontSize: 12, color: Theme.of(context).hintColor)),
                    ]),
                  ),
                ),
                IconButton(onPressed: _fontSheet, icon: const Icon(Icons.text_fields_rounded)),
                IconButton(
                  onPressed: () => lib.toggleBookmark(doc),
                  icon: AnimatedSwitcher(
                    duration: const Duration(milliseconds: 250),
                    transitionBuilder: (c, a) => ScaleTransition(scale: a, child: c),
                    child: Icon(
                      doc.bookmarked ? Icons.bookmark_rounded : Icons.bookmark_border_rounded,
                      key: ValueKey(doc.bookmarked),
                      color: doc.bookmarked ? VColors.gold : null,
                    ),
                  ),
                ),
                PopupMenuButton<String>(
                  icon: const Icon(Icons.more_vert_rounded),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(18)),
                  onSelected: (v) async {
                    if (v == 'copy') {
                      await Clipboard.setData(ClipboardData(text: _viewText));
                      if (context.mounted) toast(context, 'Copy ho gaya ✓');
                    } else if (v == 'rename') {
                      _rename();
                    } else if (v == 'share') {
                      SharePlus.instance.share(ShareParams(text: _viewText));
                    } else if (v == 'delete') {
                      lib.remove(doc);
                      Navigator.pop(context);
                    }
                  },
                  itemBuilder: (_) => const [
                    PopupMenuItem(value: 'rename', child: Text('✏️  Naam badlo')),
                    PopupMenuItem(value: 'copy', child: Text('📋  Text copy karo')),
                    PopupMenuItem(value: 'share', child: Text('📤  Text share karo')),
                    PopupMenuItem(value: 'delete', child: Text('🗑️  Delete karo')),
                  ],
                ),
              ]),
            ),

            // ---------------------------------------------------------------- AI actions
            SizedBox(
              height: 52,
              child: ListView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                children: [
                  _ActionChip(icon: Icons.auto_awesome_rounded, label: 'AI se Poocho', gradient: VColors.brand, onTap: () {
                    Navigator.push(context, MaterialPageRoute(builder: (_) => AskScreen(doc: doc)));
                  }),
                  _ActionChip(icon: Icons.summarize_rounded, label: 'Chhota Saar', gradient: VColors.warm, onTap: _summary),
                  _ActionChip(
                    icon: Icons.translate_rounded,
                    label: 'Translate karke suno',
                    gradient: const LinearGradient(colors: [Color(0xFF8B5CF6), Color(0xFFEC4899)]),
                    onTap: _translate,
                  ),
                  _ActionChip(
                    icon: Icons.download_rounded,
                    label: 'MP3 / WhatsApp',
                    gradient: const LinearGradient(colors: [Color(0xFF25D366), Color(0xFF128C7E)]),
                    onTap: _download,
                  ),
                ].animate(interval: 60.ms).fadeIn(duration: 300.ms).slideX(begin: 0.3),
              ),
            ),

            // ---------------------------------------------------------------- view tabs
            if (modes.length > 1)
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 6, 16, 0),
                child: Row(children: [
                  for (final m in modes)
                    Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: ChoiceChip(
                        label: Text(switch (m) {
                          ViewMode.original => 'Asli Page',
                          ViewMode.translation => 'Anuvaad',
                          ViewMode.summary => 'Saar',
                        }),
                        selected: _mode == m,
                        onSelected: (_) => setState(() => _mode = m),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                      ),
                    ),
                ]),
              ),

            // ---------------------------------------------------------------- text
            Expanded(
              child: Stack(children: [
                SingleChildScrollView(
                  padding: const EdgeInsets.fromLTRB(16, 10, 16, 300),
                  child: Glass(
                    padding: const EdgeInsets.fromLTRB(20, 18, 20, 22),
                    child: AnimatedSwitcher(
                      duration: const Duration(milliseconds: 350),
                      child: SelectableText(
                        _viewText,
                        key: ValueKey(_mode),
                        style: VTheme.reader(context, scale),
                        onSelectionChanged: (sel, _) {
                          final t = sel.isCollapsed ? '' : sel.textInside(_viewText);
                          if (t != _selected) setState(() => _selected = t);
                        },
                        contextMenuBuilder: (ctx, state) {
                          final sel = state.textEditingValue.selection;
                          final txt = sel.isCollapsed ? '' : sel.textInside(state.textEditingValue.text);
                          return AdaptiveTextSelectionToolbar.buttonItems(
                            anchors: state.contextMenuAnchors,
                            buttonItems: [
                              ContextMenuButtonItem(
                                label: '🔊 Sunao',
                                onPressed: () {
                                  ContextMenuController.removeAny();
                                  _speak(txt, label: 'Selected • ${doc.title}');
                                },
                              ),
                              ...state.contextMenuButtonItems,
                            ],
                          );
                        },
                      ),
                    ),
                  ),
                ),

                // Select kiya hua sunne ka button
                Positioned(
                  left: 0,
                  right: 0,
                  bottom: 250,
                  child: Center(
                    child: AnimatedSwitcher(
                      duration: const Duration(milliseconds: 250),
                      transitionBuilder: (c, a) => ScaleTransition(scale: a, child: FadeTransition(opacity: a, child: c)),
                      child: _selected.trim().isEmpty
                          ? const SizedBox.shrink()
                          : Pressable(
                              key: const ValueKey('sel'),
                              onTap: () => _speak(_selected, label: 'Selected • ${doc.title}'),
                              child: Container(
                                padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 13),
                                decoration: BoxDecoration(
                                  gradient: VColors.warm,
                                  borderRadius: BorderRadius.circular(30),
                                  boxShadow: [BoxShadow(color: VColors.coral.withValues(alpha: 0.5), blurRadius: 20, offset: const Offset(0, 8))],
                                ),
                                child: const Row(mainAxisSize: MainAxisSize.min, children: [
                                  Icon(Icons.record_voice_over_rounded, color: Colors.white),
                                  SizedBox(width: 8),
                                  Text('Sirf select kiya hua suno', style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700)),
                                ]),
                              ),
                            ),
                    ),
                  ),
                ),

                // ---------------------------------------------------------------- player
                Positioned(
                  left: 14,
                  right: 14,
                  bottom: 0,
                  child: SafeArea(
                    top: false,
                    child: Padding(
                      padding: const EdgeInsets.only(bottom: 10),
                      child: Consumer<VoicePlayer>(
                        builder: (_, player, __) => PlayerPanel(onPlay: _onPlay, isMine: _isMine(player), onDownload: _download),
                      ),
                    ),
                  ).animate().slideY(begin: 1, duration: 500.ms, curve: Curves.easeOutCubic),
                ),
              ]),
            ),
          ]),
        ),
      ),
    );
  }
}

class _ActionChip extends StatelessWidget {
  const _ActionChip({required this.icon, required this.label, required this.gradient, required this.onTap});
  final IconData icon;
  final String label;
  final Gradient gradient;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(right: 10),
        child: Pressable(
          onTap: onTap,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 14),
            decoration: BoxDecoration(gradient: gradient, borderRadius: BorderRadius.circular(20)),
            alignment: Alignment.center,
            child: Row(mainAxisSize: MainAxisSize.min, children: [
              Icon(icon, color: Colors.white, size: 18),
              const SizedBox(width: 7),
              Text(label, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 13.5)),
            ]),
          ),
        ),
      );
}
