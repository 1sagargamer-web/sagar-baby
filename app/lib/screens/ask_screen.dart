import 'package:flutter_animate/flutter_animate.dart';
import 'package:material_ui/material_ui.dart';
import 'package:provider/provider.dart';

import '../core/theme.dart';
import '../services/api.dart';
import '../services/backend.dart';
import '../services/library.dart';
import '../services/player.dart';
import '../widgets/common.dart';

class _Msg {
  _Msg(this.q);
  final String q;
  String? a;
  bool failed = false;
}

/// Page ke baare mein sawaal poocho - jawab Sagar ki awaaz mein.
class AskScreen extends StatefulWidget {
  const AskScreen({super.key, required this.doc});
  final VaaniDoc doc;

  @override
  State<AskScreen> createState() => _AskScreenState();
}

class _AskScreenState extends State<AskScreen> {
  final _ctrl = TextEditingController();
  final _scroll = ScrollController();
  final List<_Msg> _msgs = [];
  bool _busy = false;
  bool _autoSpeak = true;

  static const _suggest = [
    'Is page ka main point kya hai?',
    'Isko simple bhasha mein samjhao',
    'Important words ka matlab batao',
    'Isse 3 sawaal banao exam ke liye',
  ];

  Future<void> _ask(String q) async {
    q = q.trim();
    if (q.isEmpty || _busy) return;
    _ctrl.clear();
    final m = _Msg(q);
    setState(() {
      _msgs.add(m);
      _busy = true;
    });
    _toEnd();
    final api = context.read<Api>();
    context.read<Backend>().log('ask_ai', q);
    try {
      final history = _msgs.where((x) => x.a != null && x != m).map((x) => {'q': x.q, 'a': x.a!}).toList();
      final a = await api.ai('ask', widget.doc.text, question: q, history: history);
      m.a = a;
      if (_autoSpeak && mounted) context.read<VoicePlayer>().speak(a, title: 'Jawab • ${widget.doc.title}');
    } catch (e) {
      m.a = e is ApiException ? e.message : 'Jawab nahi aa paya, dobara poocho.';
      m.failed = true;
    } finally {
      if (mounted) setState(() => _busy = false);
      _toEnd();
    }
  }

  void _toEnd() => Future.delayed(const Duration(milliseconds: 120), () {
        if (_scroll.hasClients) {
          _scroll.animateTo(_scroll.position.maxScrollExtent + 200, duration: const Duration(milliseconds: 400), curve: Curves.easeOutCubic);
        }
      });

  @override
  Widget build(BuildContext context) {
    final player = context.watch<VoicePlayer>();
    return Scaffold(
      body: OceanBackground(
        child: SafeArea(
          child: Column(children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(6, 4, 12, 4),
              child: Row(children: [
                IconButton(onPressed: () => Navigator.pop(context), icon: const Icon(Icons.arrow_back_ios_new_rounded)),
                const IconBubble(icon: Icons.auto_awesome_rounded, size: 40),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                    const Text('AI se Poocho', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
                    Text(widget.doc.title, maxLines: 1, overflow: TextOverflow.ellipsis, style: TextStyle(fontSize: 12, color: Theme.of(context).hintColor)),
                  ]),
                ),
                Tooltip(
                  message: 'Jawab apne aap bole',
                  child: Row(children: [
                    const Icon(Icons.record_voice_over_rounded, size: 18),
                    Switch(value: _autoSpeak, onChanged: (v) => setState(() => _autoSpeak = v)),
                  ]),
                ),
              ]),
            ),
            Expanded(
              child: _msgs.isEmpty
                  ? _Empty(onPick: _ask)
                  : ListView.builder(
                      controller: _scroll,
                      padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
                      itemCount: _msgs.length + (_busy ? 1 : 0),
                      itemBuilder: (_, i) {
                        if (i == _msgs.length) return const _Typing();
                        final m = _msgs[i];
                        return Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                          _Bubble(text: m.q, me: true),
                          if (m.a != null)
                            _Bubble(
                              text: m.a!,
                              me: false,
                              failed: m.failed,
                              speaking: player.currentText == m.a!.trim() && player.isPlaying,
                              onSpeak: m.failed
                                  ? null
                                  : () {
                                      final p = context.read<VoicePlayer>();
                                      p.currentText == m.a!.trim() ? p.toggle() : p.speak(m.a!, title: 'Jawab • ${widget.doc.title}');
                                    },
                            ),
                        ]);
                      },
                    ),
            ),
            Padding(
              padding: EdgeInsets.fromLTRB(14, 6, 14, 12 + MediaQuery.of(context).padding.bottom * 0),
              child: Glass(
                radius: 30,
                padding: const EdgeInsets.fromLTRB(18, 4, 6, 4),
                child: Row(children: [
                  Expanded(
                    child: TextField(
                      controller: _ctrl,
                      minLines: 1,
                      maxLines: 4,
                      textInputAction: TextInputAction.send,
                      onSubmitted: _ask,
                      decoration: const InputDecoration(
                        hintText: 'Apna sawaal likho…',
                        filled: false,
                        border: InputBorder.none,
                        contentPadding: EdgeInsets.symmetric(vertical: 14),
                      ),
                    ),
                  ),
                  Pressable(
                    onTap: () => _ask(_ctrl.text),
                    child: Container(
                      width: 48,
                      height: 48,
                      decoration: const BoxDecoration(shape: BoxShape.circle, gradient: VColors.brand),
                      child: _busy
                          ? const Padding(padding: EdgeInsets.all(14), child: CircularProgressIndicator(strokeWidth: 2.4, color: Colors.white))
                          : const Icon(Icons.send_rounded, color: Colors.white),
                    ),
                  ),
                ]),
              ),
            ),
          ]),
        ),
      ),
    );
  }
}

class _Empty extends StatelessWidget {
  const _Empty({required this.onPick});
  final ValueChanged<String> onPick;

  @override
  Widget build(BuildContext context) => ListView(padding: const EdgeInsets.all(24), children: [
        const SizedBox(height: 20),
        const Center(child: VaaniLogo(size: 90)),
        const SizedBox(height: 22),
        const Text('Is page ke baare mein kuch bhi poocho', textAlign: TextAlign.center, style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700)),
        const SizedBox(height: 6),
        Text('Jawab Sagar ki awaaz mein bhi sunoge 🔊', textAlign: TextAlign.center, style: TextStyle(color: Theme.of(context).hintColor)),
        const SizedBox(height: 26),
        for (final s in _AskScreenState._suggest)
          Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: Glass(
              onTap: () => onPick(s),
              padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 15),
              radius: 20,
              child: Row(children: [
                const Icon(Icons.lightbulb_outline_rounded, color: VColors.gold),
                const SizedBox(width: 12),
                Expanded(child: Text(s, style: const TextStyle(fontWeight: FontWeight.w500))),
                const Icon(Icons.north_east_rounded, size: 18),
              ]),
            ),
          ),
      ].animate(interval: 50.ms).fadeIn(duration: 300.ms).slideY(begin: 0.2));
}

class _Bubble extends StatelessWidget {
  const _Bubble({required this.text, required this.me, this.onSpeak, this.speaking = false, this.failed = false});
  final String text;
  final bool me, speaking, failed;
  final VoidCallback? onSpeak;

  @override
  Widget build(BuildContext context) {
    final dark = isDark(context);
    return Align(
      alignment: me ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        constraints: BoxConstraints(maxWidth: MediaQuery.of(context).size.width * 0.82),
        padding: const EdgeInsets.fromLTRB(16, 12, 16, 12),
        decoration: BoxDecoration(
          gradient: me ? VColors.brand : null,
          color: me ? null : (failed ? VColors.coral.withValues(alpha: 0.15) : (dark ? Colors.white.withValues(alpha: 0.08) : Colors.white)),
          borderRadius: BorderRadius.only(
            topLeft: const Radius.circular(22),
            topRight: const Radius.circular(22),
            bottomLeft: Radius.circular(me ? 22 : 6),
            bottomRight: Radius.circular(me ? 6 : 22),
          ),
        ),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          SelectableText(text, style: VTheme.reader(context, 0.88).copyWith(color: me ? Colors.white : null)),
          if (onSpeak != null) ...[
            const SizedBox(height: 6),
            GestureDetector(
              onTap: onSpeak,
              child: Row(mainAxisSize: MainAxisSize.min, children: [
                Icon(speaking ? Icons.pause_circle_rounded : Icons.volume_up_rounded, size: 20, color: VColors.aqua),
                const SizedBox(width: 6),
                Text(speaking ? 'Bol raha hoon…' : 'Suno', style: const TextStyle(color: VColors.aqua, fontWeight: FontWeight.w600, fontSize: 13)),
              ]),
            ),
          ],
        ]),
      ).animate().fadeIn(duration: 250.ms).slideY(begin: 0.2, curve: Curves.easeOutCubic),
    );
  }
}

class _Typing extends StatelessWidget {
  const _Typing();

  @override
  Widget build(BuildContext context) => Align(
        alignment: Alignment.centerLeft,
        child: Container(
          margin: const EdgeInsets.only(bottom: 10),
          padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 16),
          decoration: BoxDecoration(
            color: isDark(context) ? Colors.white.withValues(alpha: 0.08) : Colors.white,
            borderRadius: BorderRadius.circular(22),
          ),
          child: Row(mainAxisSize: MainAxisSize.min, children: [
            for (var i = 0; i < 3; i++)
              Container(
                width: 8,
                height: 8,
                margin: const EdgeInsets.symmetric(horizontal: 3),
                decoration: const BoxDecoration(shape: BoxShape.circle, color: VColors.aqua),
              ).animate(onPlay: (c) => c.repeat(), delay: (i * 150).ms).moveY(begin: 0, end: -6, duration: 400.ms).then().moveY(begin: -6, end: 0, duration: 400.ms),
          ]),
        ),
      );
}
