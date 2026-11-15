import 'dart:math' as math;
import 'dart:ui';

import 'package:flutter/services.dart';
import 'package:material_ui/material_ui.dart';

import '../core/theme.dart';

bool isDark(BuildContext c) => Theme.of(c).brightness == Brightness.dark;

void toast(BuildContext context, String msg) {
  ScaffoldMessenger.of(context)
    ..hideCurrentSnackBar()
    ..showSnackBar(SnackBar(content: Text(msg)));
}

/// Dheere-dheere hilne wale glowing "samundar" blobs - poore app ka background.
class OceanBackground extends StatefulWidget {
  const OceanBackground({super.key, required this.child});
  final Widget child;

  @override
  State<OceanBackground> createState() => _OceanBackgroundState();
}

class _OceanBackgroundState extends State<OceanBackground> with SingleTickerProviderStateMixin {
  late final AnimationController _c = AnimationController(vsync: this, duration: const Duration(seconds: 18))..repeat();

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final dark = isDark(context);
    return Stack(children: [
      Positioned.fill(child: ColoredBox(color: dark ? VColors.darkBg : VColors.lightBg)),
      Positioned.fill(
        child: RepaintBoundary(
          child: AnimatedBuilder(
            animation: _c,
            builder: (_, __) => CustomPaint(painter: _BlobPainter(_c.value, dark)),
          ),
        ),
      ),
      Positioned.fill(
        child: BackdropFilter(filter: ImageFilter.blur(sigmaX: 60, sigmaY: 60), child: const SizedBox()),
      ),
      Positioned.fill(child: widget.child),
    ]);
  }
}

class _BlobPainter extends CustomPainter {
  _BlobPainter(this.t, this.dark);
  final double t;
  final bool dark;

  @override
  void paint(Canvas canvas, Size s) {
    final a = t * 2 * math.pi;
    final o = dark ? 0.45 : 0.28;
    void blob(Color c, double x, double y, double r) {
      canvas.drawCircle(
        Offset(x * s.width, y * s.height),
        r * s.width,
        Paint()..color = c.withValues(alpha: o),
      );
    }

    blob(VColors.aqua, 0.15 + 0.08 * math.sin(a), 0.12 + 0.05 * math.cos(a), 0.42);
    blob(VColors.ocean, 0.9 + 0.07 * math.cos(a * 1.3), 0.35 + 0.08 * math.sin(a), 0.45);
    blob(VColors.violet, 0.3 + 0.1 * math.cos(a * 0.7), 0.95 + 0.04 * math.sin(a * 1.1), 0.5);
  }

  @override
  bool shouldRepaint(covariant _BlobPainter old) => old.t != t || old.dark != dark;
}

/// Frosted glass card.
class Glass extends StatelessWidget {
  const Glass({super.key, required this.child, this.padding = const EdgeInsets.all(18), this.radius = 26, this.onTap});
  final Widget child;
  final EdgeInsets padding;
  final double radius;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final dark = isDark(context);
    final card = ClipRRect(
      borderRadius: BorderRadius.circular(radius),
      child: BackdropFilter(
        filter: ImageFilter.blur(sigmaX: 18, sigmaY: 18),
        child: Container(
          padding: padding,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(radius),
            color: dark ? Colors.white.withValues(alpha: 0.07) : Colors.white.withValues(alpha: 0.72),
            border: Border.all(color: dark ? Colors.white.withValues(alpha: 0.10) : Colors.white),
          ),
          child: child,
        ),
      ),
    );
    return onTap == null ? card : Pressable(onTap: onTap!, child: card);
  }
}

/// Dabane pe halka sa chhota hota hai + haptic - premium feel.
class Pressable extends StatefulWidget {
  const Pressable({super.key, required this.child, required this.onTap, this.onLongPress});
  final Widget child;
  final VoidCallback onTap;
  final VoidCallback? onLongPress;

  @override
  State<Pressable> createState() => _PressableState();
}

class _PressableState extends State<Pressable> {
  bool _down = false;

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      behavior: HitTestBehavior.opaque,
      onTapDown: (_) => setState(() => _down = true),
      onTapCancel: () => setState(() => _down = false),
      onTapUp: (_) => setState(() => _down = false),
      onTap: () {
        HapticFeedback.selectionClick();
        widget.onTap();
      },
      onLongPress: widget.onLongPress,
      child: AnimatedScale(
        scale: _down ? 0.95 : 1,
        duration: const Duration(milliseconds: 120),
        curve: Curves.easeOut,
        child: widget.child,
      ),
    );
  }
}

class GradientButton extends StatelessWidget {
  const GradientButton({
    super.key,
    required this.label,
    required this.onTap,
    this.icon,
    this.loading = false,
    this.gradient = VColors.brand,
    this.height = 58,
  });
  final String label;
  final IconData? icon;
  final VoidCallback? onTap;
  final bool loading;
  final Gradient gradient;
  final double height;

  @override
  Widget build(BuildContext context) {
    return Pressable(
      onTap: loading || onTap == null ? () {} : onTap!,
      child: AnimatedOpacity(
        duration: const Duration(milliseconds: 200),
        opacity: onTap == null ? 0.5 : 1,
        child: Container(
          height: height,
          decoration: BoxDecoration(
            gradient: gradient,
            borderRadius: BorderRadius.circular(height / 2),
            boxShadow: [BoxShadow(color: VColors.ocean.withValues(alpha: 0.35), blurRadius: 24, offset: const Offset(0, 10))],
          ),
          alignment: Alignment.center,
          child: loading
              ? const SizedBox(width: 24, height: 24, child: CircularProgressIndicator(strokeWidth: 2.6, color: Colors.white))
              : Row(mainAxisSize: MainAxisSize.min, children: [
                  if (icon != null) ...[Icon(icon, color: Colors.white), const SizedBox(width: 10)],
                  Text(label, style: const TextStyle(color: Colors.white, fontWeight: FontWeight.w600, fontSize: 16)),
                ]),
        ),
      ),
    );
  }
}

class GradientText extends StatelessWidget {
  const GradientText(this.text, {super.key, required this.style, this.gradient = VColors.brand});
  final String text;
  final TextStyle style;
  final Gradient gradient;

  @override
  Widget build(BuildContext context) => ShaderMask(
        blendMode: BlendMode.srcIn,
        shaderCallback: (r) => gradient.createShader(Rect.fromLTWH(0, 0, r.width, r.height)),
        child: Text(text, style: style),
      );
}

/// Bolte waqt naachti lehrein (sound waves).
class WaveVisualizer extends StatefulWidget {
  const WaveVisualizer({super.key, required this.active, this.height = 56, this.color});
  final bool active;
  final double height;
  final Color? color;

  @override
  State<WaveVisualizer> createState() => _WaveVisualizerState();
}

class _WaveVisualizerState extends State<WaveVisualizer> with SingleTickerProviderStateMixin {
  late final AnimationController _c = AnimationController(vsync: this, duration: const Duration(milliseconds: 1400))..repeat();
  double _amp = 0.15;

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return TweenAnimationBuilder<double>(
      tween: Tween(end: widget.active ? 1 : 0.15),
      duration: const Duration(milliseconds: 500),
      builder: (_, amp, __) {
        _amp = amp;
        return SizedBox(
          height: widget.height,
          width: double.infinity,
          child: AnimatedBuilder(
            animation: _c,
            builder: (_, __) => CustomPaint(painter: _WavePainter(_c.value, _amp, widget.color)),
          ),
        );
      },
    );
  }
}

class _WavePainter extends CustomPainter {
  _WavePainter(this.t, this.amp, this.color);
  final double t, amp;
  final Color? color;

  @override
  void paint(Canvas canvas, Size s) {
    final colors = [VColors.aqua, VColors.ocean, VColors.violet];
    for (var w = 0; w < 3; w++) {
      final path = Path();
      final phase = t * 2 * math.pi + w * 1.3;
      for (double x = 0; x <= s.width; x += 3) {
        final nx = x / s.width;
        final env = math.sin(nx * math.pi); // beech mein unchi
        final y = s.height / 2 +
            math.sin(nx * 4 * math.pi + phase) * (s.height / 2.4) * amp * env * (1 - w * 0.22);
        x == 0 ? path.moveTo(x, y) : path.lineTo(x, y);
      }
      canvas.drawPath(
        path,
        Paint()
          ..style = PaintingStyle.stroke
          ..strokeWidth = 2.6 - w * 0.5
          ..strokeCap = StrokeCap.round
          ..color = (color ?? colors[w]).withValues(alpha: 0.9 - w * 0.25),
      );
    }
  }

  @override
  bool shouldRepaint(covariant _WavePainter o) => true;
}

/// App logo - lehron wala gol nishaan.
class VaaniLogo extends StatefulWidget {
  const VaaniLogo({super.key, this.size = 96, this.spin = true});
  final double size;
  final bool spin;

  @override
  State<VaaniLogo> createState() => _VaaniLogoState();
}

class _VaaniLogoState extends State<VaaniLogo> with SingleTickerProviderStateMixin {
  late final AnimationController _c = AnimationController(vsync: this, duration: const Duration(seconds: 3));

  @override
  void initState() {
    super.initState();
    if (widget.spin) _c.repeat();
  }

  @override
  void dispose() {
    _c.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final s = widget.size;
    return AnimatedBuilder(
      animation: _c,
      builder: (_, __) {
        final pulse = 1 + 0.05 * math.sin(_c.value * 2 * math.pi);
        return Transform.scale(
          scale: pulse,
          child: Container(
            width: s,
            height: s,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              gradient: SweepGradient(
                colors: const [VColors.aqua, VColors.ocean, VColors.violet, VColors.aqua],
                transform: GradientRotation(_c.value * 2 * math.pi),
              ),
              boxShadow: [BoxShadow(color: VColors.aqua.withValues(alpha: 0.45), blurRadius: s * 0.45)],
            ),
            padding: EdgeInsets.all(s * 0.05),
            child: Container(
              decoration: const BoxDecoration(shape: BoxShape.circle, color: Color(0xFF081032)),
              child: ClipOval(
                child: Padding(
                  padding: EdgeInsets.symmetric(horizontal: s * 0.14),
                  child: CustomPaint(painter: _WavePainter(_c.value, 0.9, null)),
                ),
              ),
            ),
          ),
        );
      },
    );
  }
}

class SectionTitle extends StatelessWidget {
  const SectionTitle(this.text, {super.key, this.trailing});
  final String text;
  final Widget? trailing;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.fromLTRB(4, 22, 4, 12),
        child: Row(children: [
          Expanded(child: Text(text, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w700))),
          if (trailing != null) trailing!,
        ]),
      );
}

class IconBubble extends StatelessWidget {
  const IconBubble({super.key, required this.icon, this.gradient = VColors.brand, this.size = 52});
  final IconData icon;
  final Gradient gradient;
  final double size;

  @override
  Widget build(BuildContext context) => Container(
        width: size,
        height: size,
        decoration: BoxDecoration(
          gradient: gradient,
          borderRadius: BorderRadius.circular(size * 0.34),
          boxShadow: [BoxShadow(color: gradient.colors.first.withValues(alpha: 0.4), blurRadius: 16, offset: const Offset(0, 6))],
        ),
        child: Icon(icon, color: Colors.white, size: size * 0.5),
      );
}

/// Kaam chalte waqt poori screen pe sundar loading.
Future<T?> runWithLoader<T>(BuildContext context, String message, Future<T> Function() job) async {
  final nav = Navigator.of(context, rootNavigator: true);
  showGeneralDialog(
    context: context,
    barrierDismissible: false,
    barrierColor: Colors.black54,
    transitionDuration: const Duration(milliseconds: 250),
    pageBuilder: (_, __, ___) => PopScope(
      canPop: false,
      child: Center(
        child: Glass(
          padding: const EdgeInsets.symmetric(horizontal: 30, vertical: 26),
          child: Column(mainAxisSize: MainAxisSize.min, children: [
            const VaaniLogo(size: 74),
            const SizedBox(height: 18),
            Material(
              type: MaterialType.transparency,
              child: Text(message, textAlign: TextAlign.center, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
            ),
          ]),
        ),
      ),
    ),
    transitionBuilder: (_, a, __, child) => FadeTransition(
      opacity: a,
      child: ScaleTransition(scale: Tween(begin: 0.9, end: 1.0).animate(CurvedAnimation(parent: a, curve: Curves.easeOutBack)), child: child),
    ),
  );
  try {
    return await job();
  } finally {
    nav.pop();
  }
}
