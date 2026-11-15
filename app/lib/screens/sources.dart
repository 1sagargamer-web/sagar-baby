import 'dart:io';

import 'package:file_picker/file_picker.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';
import 'package:material_ui/material_ui.dart';
import 'package:provider/provider.dart';

import '../services/api.dart';
import '../services/backend.dart';
import '../services/extract.dart';
import '../services/library.dart';
import '../widgets/common.dart';
import 'reader_screen.dart';
import 'scan_screen.dart';

/// Page andar laane ke saare tareeke: Camera, Photo, PDF, Text, Link.
class Sources {
  static Future<void> _finish(BuildContext context, String text, String source, {String? title}) async {
    if (!context.mounted) return;
    if (text.trim().isEmpty) {
      toast(context, 'Is page pe koi text nahi mila 😕');
      return;
    }
    final doc = context.read<LibraryStore>().create(text.trim(), source, title: title);
    context.read<Backend>().log('page_$source', doc.title);
    await Navigator.of(context).push(MaterialPageRoute(builder: (_) => ReaderScreen(doc: doc, autoPlay: true)));
  }

  static String _errText(Object e) => e is ApiException ? e.message : 'Text nahi nikal paya. Dobara try karein.';

  static Future<void> camera(BuildContext context) async {
    final files = await Navigator.of(context).push<List<File>>(MaterialPageRoute(builder: (_) => const ScanScreen()));
    if (files == null || files.isEmpty || !context.mounted) return;
    await images(context, files, 'camera');
  }

  static Future<void> photos(BuildContext context) async {
    final picked = await ImagePicker().pickMultiImage(imageQuality: 88, maxWidth: 2600);
    if (picked.isEmpty || !context.mounted) return;
    await images(context, picked.map((x) => File(x.path)).toList(), 'photo');
  }

  static Future<void> images(BuildContext context, List<File> files, String source) async {
    final ex = context.read<Extractor>();
    try {
      final text = await runWithLoader(
        context,
        files.length > 1 ? '${files.length} page padh raha hoon…\nHandwriting bhi samajh raha hoon ✍️' : 'Page padh raha hoon…',
        () => ex.fromImages(files),
      );
      if (context.mounted) await _finish(context, text ?? '', source);
    } catch (e) {
      if (context.mounted) toast(context, _errText(e));
    }
  }

  static Future<void> pdf(BuildContext context) async {
    final files = await FilePicker.pickFiles(type: FileType.custom, allowedExtensions: ['pdf']);
    if (files.isEmpty || !context.mounted) return;
    final ex = context.read<Extractor>();
    try {
      final text = await runWithLoader(context, 'PDF khol ke padh raha hoon…', () async {
        final out = <String>[];
        for (final f in files) {
          if (f.path == null) continue;
          out.add(await ex.fromPdf(File(f.path!)));
        }
        return out.where((t) => t.isNotEmpty).join('\n\n');
      });
      final title = files.length == 1 ? files.first.name.replaceAll(RegExp(r'\.pdf$', caseSensitive: false), '') : null;
      if (context.mounted) await _finish(context, text ?? '', 'pdf', title: title);
    } catch (e) {
      if (context.mounted) toast(context, _errText(e));
    }
  }

  static Future<void> link(BuildContext context) async {
    final ctrl = TextEditingController();
    final clip = await Clipboard.getData('text/plain');
    if ((clip?.text ?? '').startsWith('http')) ctrl.text = clip!.text!.trim();
    if (!context.mounted) return;
    final url = await showModalBottomSheet<String>(
      context: context,
      isScrollControlled: true,
      builder: (c) => _InputSheet(
        title: 'Website ka link',
        hint: 'https://…',
        icon: Icons.link_rounded,
        controller: ctrl,
        maxLines: 1,
        button: 'Page kholo',
      ),
    );
    if (url == null || url.trim().isEmpty || !context.mounted) return;
    final ex = context.read<Extractor>();
    try {
      final text = await runWithLoader(context, 'Website se text la raha hoon…', () => ex.fromLink(url));
      if (context.mounted) await _finish(context, text ?? '', 'link');
    } catch (e) {
      if (context.mounted) toast(context, e is ApiException ? e.message : 'Ye link nahi khul paya');
    }
  }

  static Future<void> text(BuildContext context) async {
    final ctrl = TextEditingController();
    final t = await showModalBottomSheet<String>(
      context: context,
      isScrollControlled: true,
      builder: (c) => _InputSheet(
        title: 'Text likho ya paste karo',
        hint: 'Yahan Hindi ya English text daaliye…',
        icon: Icons.edit_note_rounded,
        controller: ctrl,
        maxLines: 10,
        button: 'Aage badho',
        showPaste: true,
      ),
    );
    if (t == null || t.trim().isEmpty || !context.mounted) return;
    await _finish(context, t, 'text');
  }
}

class _InputSheet extends StatelessWidget {
  const _InputSheet({
    required this.title,
    required this.hint,
    required this.icon,
    required this.controller,
    required this.maxLines,
    required this.button,
    this.showPaste = false,
  });

  final String title, hint, button;
  final IconData icon;
  final TextEditingController controller;
  final int maxLines;
  final bool showPaste;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.fromLTRB(22, 14, 22, MediaQuery.of(context).viewInsets.bottom + 22),
      child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Center(child: Container(width: 44, height: 5, decoration: BoxDecoration(color: Theme.of(context).hintColor.withValues(alpha: 0.3), borderRadius: BorderRadius.circular(3)))),
        const SizedBox(height: 18),
        Row(children: [
          IconBubble(icon: icon, size: 42),
          const SizedBox(width: 12),
          Expanded(child: Text(title, style: const TextStyle(fontSize: 19, fontWeight: FontWeight.w700))),
          if (showPaste)
            TextButton.icon(
              onPressed: () async {
                final c = await Clipboard.getData('text/plain');
                if (c?.text != null) controller.text = c!.text!;
              },
              icon: const Icon(Icons.content_paste_rounded, size: 18),
              label: const Text('Paste'),
            ),
        ]),
        const SizedBox(height: 16),
        TextField(controller: controller, autofocus: true, maxLines: maxLines, minLines: maxLines > 1 ? 5 : 1, decoration: InputDecoration(hintText: hint)),
        const SizedBox(height: 18),
        GradientButton(label: button, icon: Icons.arrow_forward_rounded, onTap: () => Navigator.pop(context, controller.text)),
      ]),
    );
  }
}
