import 'package:material_ui/material_ui.dart';
import 'package:provider/provider.dart';

import '../core/theme.dart';
import '../services/player.dart';
import '../services/settings.dart';
import 'common.dart';

const speeds = [0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0];

String speedLabel(double s) => '${s == s.roundToDouble() ? s.toStringAsFixed(0) : s.toString()}x';

Future<void> pickSpeed(BuildContext context) async {
  final p = context.read<VoicePlayer>();
  final s = context.read<SettingsStore>();
  await showModalBottomSheet(
    context: context,
    builder: (c) => SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(22, 18, 22, 22),
        child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.start, children: [
          const Text('Bolne ki speed', style: TextStyle(fontSize: 19, fontWeight: FontWeight.w700)),
          const SizedBox(height: 4),
          Text('Dheere ya tez - jaisa aapko pasand', style: TextStyle(color: Theme.of(c).hintColor)),
          const SizedBox(height: 18),
          Wrap(spacing: 10, runSpacing: 10, children: [
            for (final v in speeds)
              Pressable(
                onTap: () {
                  p.setSpeed(v);
                  s.setSpeed(v);
                  Navigator.pop(c);
                },
                child: AnimatedContainer(
                  duration: const Duration(milliseconds: 200),
                  padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 12),
                  decoration: BoxDecoration(
                    gradient: p.speed == v ? VColors.brand : null,
                    color: p.speed == v ? null : Theme.of(c).hintColor.withValues(alpha: 0.1),
                    borderRadius: BorderRadius.circular(16),
                  ),
                  child: Text(
                    v == 1.0 ? '1x Normal' : speedLabel(v),
                    style: TextStyle(fontWeight: FontWeight.w700, color: p.speed == v ? Colors.white : null),
                  ),
                ),
              ),
          ]),
        ]),
      ),
    ),
  );
}

/// Bada player: lehrein + progress + controls.
class PlayerPanel extends StatelessWidget {
  const PlayerPanel({super.key, required this.onPlay, required this.isMine, required this.onDownload});
  final VoidCallback onPlay;
  final bool isMine;
  final VoidCallback onDownload;

  @override
  Widget build(BuildContext context) {
    final p = context.watch<VoicePlayer>();
    final active = isMine && p.hasContent;
    final playing = active && p.isPlaying;
    final loading = active && (p.state == VoiceState.loading || p.state == VoiceState.waiting);
    String status;
    if (!active) {
      status = 'Play dabao - Sagar ki awaaz mein suno';
    } else {
      status = switch (p.state) {
        VoiceState.loading => 'Awaaz taiyaar ho rahi hai…',
        VoiceState.waiting => 'Agla hissa aa raha hai…',
        VoiceState.playing => 'Bol raha hoon • Part ${p.index + 1}/${p.chunks.length}',
        VoiceState.paused => 'Ruka hua • Part ${p.index + 1}/${p.chunks.length}',
        VoiceState.done => 'Pura padh liya ✓',
        VoiceState.error => p.error ?? 'Kuch gadbad hui',
        VoiceState.idle => 'Play dabao',
      };
    }

    return Glass(
      radius: 30,
      padding: const EdgeInsets.fromLTRB(18, 12, 18, 14),
      child: Column(mainAxisSize: MainAxisSize.min, children: [
        WaveVisualizer(active: playing && p.state == VoiceState.playing, height: 40),
        const SizedBox(height: 4),
        ClipRRect(
          borderRadius: BorderRadius.circular(4),
          child: TweenAnimationBuilder<double>(
            tween: Tween(end: active ? p.progress : 0),
            duration: const Duration(milliseconds: 300),
            builder: (_, v, __) => LinearProgressIndicator(
              value: v,
              minHeight: 5,
              backgroundColor: Theme.of(context).hintColor.withValues(alpha: 0.15),
              valueColor: const AlwaysStoppedAnimation(VColors.aqua),
            ),
          ),
        ),
        const SizedBox(height: 8),
        AnimatedSwitcher(
          duration: const Duration(milliseconds: 250),
          child: Text(
            status,
            key: ValueKey(status),
            maxLines: 2,
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 12.5,
              color: p.state == VoiceState.error && active ? VColors.coral : Theme.of(context).hintColor,
            ),
          ),
        ),
        const SizedBox(height: 8),
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          _SmallBtn(label: speedLabel(p.speed), onTap: () => pickSpeed(context)),
          IconButton(
            iconSize: 30,
            onPressed: active ? p.previous : null,
            icon: const Icon(Icons.skip_previous_rounded),
          ),
          Pressable(
            onTap: onPlay,
            child: Container(
              width: 70,
              height: 70,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: VColors.brand,
                boxShadow: [BoxShadow(color: VColors.ocean.withValues(alpha: 0.5), blurRadius: 22, offset: const Offset(0, 8))],
              ),
              child: loading
                  ? const Padding(padding: EdgeInsets.all(22), child: CircularProgressIndicator(strokeWidth: 3, color: Colors.white))
                  : AnimatedSwitcher(
                      duration: const Duration(milliseconds: 200),
                      transitionBuilder: (c, a) => ScaleTransition(scale: a, child: c),
                      child: Icon(
                        playing ? Icons.pause_rounded : Icons.play_arrow_rounded,
                        key: ValueKey(playing),
                        color: Colors.white,
                        size: 40,
                      ),
                    ),
            ),
          ),
          IconButton(
            iconSize: 30,
            onPressed: active ? p.next : null,
            icon: const Icon(Icons.skip_next_rounded),
          ),
          _SmallBtn(icon: Icons.download_rounded, onTap: onDownload),
        ]),
      ]),
    );
  }
}

class _SmallBtn extends StatelessWidget {
  const _SmallBtn({this.label, this.icon, required this.onTap});
  final String? label;
  final IconData? icon;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Pressable(
        onTap: onTap,
        child: Container(
          width: 54,
          height: 40,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: Theme.of(context).hintColor.withValues(alpha: 0.12),
            borderRadius: BorderRadius.circular(14),
          ),
          child: icon != null ? Icon(icon, size: 22) : Text(label!, style: const TextStyle(fontWeight: FontWeight.w700)),
        ),
      );
}

/// Home screen ke neeche chhota player (jab kuch bol raha ho).
class MiniPlayer extends StatelessWidget {
  const MiniPlayer({super.key});

  @override
  Widget build(BuildContext context) {
    final p = context.watch<VoicePlayer>();
    final show = p.hasContent && p.state != VoiceState.idle;
    return AnimatedSwitcher(
      duration: const Duration(milliseconds: 350),
      transitionBuilder: (c, a) => SizeTransition(sizeFactor: a, child: FadeTransition(opacity: a, child: c)),
      child: !show
          ? const SizedBox.shrink()
          : Padding(
              key: const ValueKey('mini'),
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 10),
              child: Glass(
                radius: 22,
                padding: const EdgeInsets.fromLTRB(14, 8, 6, 8),
                child: Row(children: [
                  SizedBox(width: 46, child: WaveVisualizer(active: p.state == VoiceState.playing, height: 30)),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisSize: MainAxisSize.min, children: [
                      Text(p.title, maxLines: 1, overflow: TextOverflow.ellipsis, style: const TextStyle(fontWeight: FontWeight.w600)),
                      Text('Part ${p.index + 1}/${p.chunks.length} • ${speedLabel(p.speed)}',
                          style: TextStyle(fontSize: 12, color: Theme.of(context).hintColor)),
                    ]),
                  ),
                  IconButton(
                    onPressed: p.toggle,
                    icon: Icon(p.isPlaying ? Icons.pause_circle_filled_rounded : Icons.play_circle_fill_rounded, size: 38, color: VColors.aqua),
                  ),
                  IconButton(onPressed: p.stop, icon: const Icon(Icons.close_rounded)),
                ]),
              ),
            ),
    );
  }
}
