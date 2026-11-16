import 'dart:io';

import 'package:camera/camera.dart';
import 'package:flutter/services.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:image_picker/image_picker.dart';
import 'package:material_ui/material_ui.dart';

import '../core/theme.dart';
import '../widgets/common.dart';

/// Live camera scan - ek ya kai page ek saath.
class ScanScreen extends StatefulWidget {
  const ScanScreen({super.key});

  @override
  State<ScanScreen> createState() => _ScanScreenState();
}

class _ScanScreenState extends State<ScanScreen> with WidgetsBindingObserver, SingleTickerProviderStateMixin {
  CameraController? _cam;
  String? _error;
  bool _flash = false;
  bool _busy = false;
  bool _flashAnim = false;
  final List<File> _pages = [];
  late final AnimationController _scan = AnimationController(vsync: this, duration: const Duration(seconds: 2))..repeat(reverse: true);

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _init();
  }

  Future<void> _init() async {
    try {
      final cams = await availableCameras();
      final back = cams.firstWhere((c) => c.lensDirection == CameraLensDirection.back, orElse: () => cams.first);
      final c = CameraController(back, ResolutionPreset.veryHigh, enableAudio: false, imageFormatGroup: ImageFormatGroup.jpeg);
      await c.initialize();
      await c.setFlashMode(FlashMode.off);
      if (!mounted) {
        await c.dispose();
        return;
      }
      setState(() => _cam = c);
    } catch (e) {
      setState(() => _error = 'Camera nahi khula. Settings mein camera permission dijiye.');
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    final c = _cam;
    if (c == null || !c.value.isInitialized) return;
    if (state == AppLifecycleState.inactive) {
      c.dispose();
      setState(() => _cam = null);
    } else if (state == AppLifecycleState.resumed) {
      _init();
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _cam?.dispose();
    _scan.dispose();
    super.dispose();
  }

  Future<void> _shoot() async {
    final c = _cam;
    if (c == null || _busy) return;
    setState(() {
      _busy = true;
      _flashAnim = true;
    });
    HapticFeedback.mediumImpact();
    try {
      final x = await c.takePicture();
      setState(() => _pages.add(File(x.path)));
    } catch (_) {
      if (mounted) toast(context, 'Photo nahi khichi, dobara try karein');
    } finally {
      if (mounted) {
        setState(() => _busy = false);
        Future.delayed(const Duration(milliseconds: 160), () => mounted ? setState(() => _flashAnim = false) : null);
      }
    }
  }

  Future<void> _gallery() async {
    final picked = await ImagePicker().pickMultiImage(imageQuality: 88, maxWidth: 2600);
    if (picked.isNotEmpty) setState(() => _pages.addAll(picked.map((e) => File(e.path))));
  }

  @override
  Widget build(BuildContext context) {
    final c = _cam;
    return Scaffold(
      backgroundColor: Colors.black,
      body: Stack(fit: StackFit.expand, children: [
        if (c != null && c.value.isInitialized)
          ClipRect(
            child: FittedBox(
              fit: BoxFit.cover,
              child: SizedBox(
                width: c.value.previewSize?.height ?? 1080,
                height: c.value.previewSize?.width ?? 1920,
                child: CameraPreview(c),
              ),
            ),
          )
        else
          Center(
            child: _error != null
                ? Padding(padding: const EdgeInsets.all(30), child: Text(_error!, textAlign: TextAlign.center, style: const TextStyle(color: Colors.white70)))
                : const CircularProgressIndicator(color: VColors.aqua),
          ),

        // Page ka frame + scan line animation
        IgnorePointer(
          child: Center(
            child: FractionallySizedBox(
              widthFactor: 0.86,
              heightFactor: 0.62,
              child: LayoutBuilder(builder: (_, box) {
                return Stack(children: [
                  Container(
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(26),
                      border: Border.all(color: Colors.white.withValues(alpha: 0.55), width: 1.4),
                    ),
                  ),
                  AnimatedBuilder(
                    animation: _scan,
                    builder: (_, __) => Positioned(
                      top: _scan.value * (box.maxHeight - 4),
                      left: 12,
                      right: 12,
                      child: Container(
                        height: 3,
                        decoration: BoxDecoration(
                          gradient: const LinearGradient(colors: [Colors.transparent, VColors.aqua, Colors.transparent]),
                          boxShadow: [BoxShadow(color: VColors.aqua.withValues(alpha: 0.8), blurRadius: 14)],
                        ),
                      ),
                    ),
                  ),
                ]);
              }),
            ),
          ),
        ),

        // Shutter flash
        IgnorePointer(
          child: AnimatedOpacity(
            opacity: _flashAnim ? 0.7 : 0,
            duration: const Duration(milliseconds: 120),
            child: const ColoredBox(color: Colors.white),
          ),
        ),

        // Upar ki bar
        SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Row(children: [
              _RoundBtn(icon: Icons.close_rounded, onTap: () => Navigator.pop(context)),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 9),
                decoration: BoxDecoration(color: Colors.black45, borderRadius: BorderRadius.circular(20)),
                child: const Text('Page ko frame mein rakho', style: TextStyle(color: Colors.white, fontSize: 13)),
              ),
              const Spacer(),
              _RoundBtn(
                icon: _flash ? Icons.flash_on_rounded : Icons.flash_off_rounded,
                onTap: () async {
                  _flash = !_flash;
                  await _cam?.setFlashMode(_flash ? FlashMode.torch : FlashMode.off);
                  setState(() {});
                },
              ),
            ]),
          ),
        ),

        // Neeche: thumbnails + shutter + done
        Positioned(
          left: 0,
          right: 0,
          bottom: 0,
          child: SafeArea(
            top: false,
            child: Padding(
              padding: const EdgeInsets.fromLTRB(20, 0, 20, 22),
              child: Column(mainAxisSize: MainAxisSize.min, children: [
                if (_pages.isNotEmpty)
                  SizedBox(
                    height: 74,
                    child: ListView.separated(
                      scrollDirection: Axis.horizontal,
                      itemCount: _pages.length,
                      separatorBuilder: (_, __) => const SizedBox(width: 10),
                      itemBuilder: (_, i) => Stack(children: [
                        ClipRRect(
                          borderRadius: BorderRadius.circular(12),
                          child: Image.file(_pages[i], width: 56, height: 74, fit: BoxFit.cover, cacheWidth: 160),
                        ),
                        Positioned(
                          right: 2,
                          top: 2,
                          child: GestureDetector(
                            onTap: () => setState(() => _pages.removeAt(i)),
                            child: const CircleAvatar(radius: 10, backgroundColor: Colors.black54, child: Icon(Icons.close, size: 12, color: Colors.white)),
                          ),
                        ),
                      ]).animate().scale(duration: 250.ms, curve: Curves.easeOutBack),
                    ),
                  ),
                const SizedBox(height: 18),
                Row(children: [
                  _RoundBtn(icon: Icons.photo_library_rounded, onTap: _gallery, size: 54),
                  const Spacer(),
                  Pressable(
                    onTap: _shoot,
                    child: Container(
                      width: 84,
                      height: 84,
                      padding: const EdgeInsets.all(5),
                      decoration: const BoxDecoration(shape: BoxShape.circle, gradient: VColors.brand),
                      child: Container(
                        decoration: BoxDecoration(shape: BoxShape.circle, color: _busy ? Colors.white70 : Colors.white),
                        child: const Icon(Icons.document_scanner_rounded, color: VColors.ocean, size: 34),
                      ),
                    ),
                  ),
                  const Spacer(),
                  AnimatedOpacity(
                    duration: const Duration(milliseconds: 250),
                    opacity: _pages.isEmpty ? 0.35 : 1,
                    child: Pressable(
                      onTap: () => _pages.isEmpty ? toast(context, 'Pehle page ki photo lo') : Navigator.pop(context, _pages),
                      child: Container(
                        height: 54,
                        padding: const EdgeInsets.symmetric(horizontal: 18),
                        decoration: BoxDecoration(color: VColors.aqua, borderRadius: BorderRadius.circular(27)),
                        alignment: Alignment.center,
                        child: Text('Padho (${_pages.length})', style: const TextStyle(color: Color(0xFF04202A), fontWeight: FontWeight.w700)),
                      ),
                    ),
                  ),
                ]),
              ]),
            ),
          ),
        ),
      ]),
    );
  }
}

class _RoundBtn extends StatelessWidget {
  const _RoundBtn({required this.icon, required this.onTap, this.size = 46});
  final IconData icon;
  final VoidCallback onTap;
  final double size;

  @override
  Widget build(BuildContext context) => Pressable(
        onTap: onTap,
        child: Container(
          width: size,
          height: size,
          decoration: BoxDecoration(color: Colors.black45, shape: BoxShape.circle, border: Border.all(color: Colors.white24)),
          child: Icon(icon, color: Colors.white),
        ),
      );
}
