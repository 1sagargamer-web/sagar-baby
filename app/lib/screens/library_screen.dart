import 'package:flutter_animate/flutter_animate.dart';
import 'package:material_ui/material_ui.dart';
import 'package:provider/provider.dart';

import '../core/theme.dart';
import '../services/library.dart';
import '../widgets/common.dart';
import 'home_shell.dart';

class LibraryScreen extends StatefulWidget {
  const LibraryScreen({super.key});

  @override
  State<LibraryScreen> createState() => _LibraryScreenState();
}

class _LibraryScreenState extends State<LibraryScreen> {
  bool _onlyBookmarks = false;
  String _q = '';

  @override
  Widget build(BuildContext context) {
    final lib = context.watch<LibraryStore>();
    var docs = _onlyBookmarks ? lib.bookmarks : lib.all;
    if (_q.isNotEmpty) {
      final q = _q.toLowerCase();
      docs = docs.where((d) => d.title.toLowerCase().contains(q) || d.text.toLowerCase().contains(q)).toList();
    }

    return SafeArea(
      bottom: false,
      child: Column(children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(18, 10, 10, 0),
          child: Row(children: [
            const Expanded(child: Text('Meri Library', style: TextStyle(fontSize: 28, fontWeight: FontWeight.w800))),
            if (lib.all.isNotEmpty)
              IconButton(
                tooltip: 'History saaf karo',
                onPressed: () async {
                  final ok = await showDialog<bool>(
                    context: context,
                    builder: (d) => AlertDialog(
                      title: const Text('History saaf karein?'),
                      content: const Text('Bookmark kiye hue page bache rahenge.'),
                      actions: [
                        TextButton(onPressed: () => Navigator.pop(d, false), child: const Text('Nahi')),
                        FilledButton(onPressed: () => Navigator.pop(d, true), child: const Text('Haan, saaf karo')),
                      ],
                    ),
                  );
                  if (ok == true) lib.clearHistory();
                },
                icon: const Icon(Icons.delete_sweep_rounded),
              ),
          ]),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(18, 12, 18, 6),
          child: TextField(
            onChanged: (v) => setState(() => _q = v),
            decoration: const InputDecoration(hintText: 'Dhoondo…', prefixIcon: Icon(Icons.search_rounded)),
          ),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(18, 6, 18, 4),
          child: Row(children: [
            _Seg(label: 'Sab (${lib.all.length})', selected: !_onlyBookmarks, onTap: () => setState(() => _onlyBookmarks = false)),
            const SizedBox(width: 10),
            _Seg(label: '★ Bookmark (${lib.bookmarks.length})', selected: _onlyBookmarks, onTap: () => setState(() => _onlyBookmarks = true)),
          ]),
        ),
        Expanded(
          child: docs.isEmpty
              ? Center(
                  child: Column(mainAxisSize: MainAxisSize.min, children: [
                    Icon(_onlyBookmarks ? Icons.bookmark_border_rounded : Icons.auto_stories_rounded, size: 70, color: Theme.of(context).hintColor.withValues(alpha: 0.4)),
                    const SizedBox(height: 12),
                    Text(_onlyBookmarks ? 'Abhi koi bookmark nahi' : 'Abhi kuch nahi padha', style: TextStyle(color: Theme.of(context).hintColor)),
                  ]).animate().fadeIn(),
                )
              : ListView.builder(
                  padding: const EdgeInsets.fromLTRB(18, 10, 18, 190),
                  itemCount: docs.length,
                  itemBuilder: (_, i) {
                    final d = docs[i];
                    return Dismissible(
                      key: ValueKey(d.id),
                      direction: DismissDirection.endToStart,
                      background: Container(
                        alignment: Alignment.centerRight,
                        padding: const EdgeInsets.only(right: 24),
                        margin: const EdgeInsets.only(bottom: 10),
                        decoration: BoxDecoration(color: VColors.coral.withValues(alpha: 0.85), borderRadius: BorderRadius.circular(22)),
                        child: const Icon(Icons.delete_rounded, color: Colors.white),
                      ),
                      onDismissed: (_) {
                        lib.remove(d);
                        toast(context, 'Delete ho gaya');
                      },
                      child: DocTile(doc: d),
                    ).animate(delay: (i.clamp(0, 10) * 40).ms).fadeIn(duration: 300.ms).slideX(begin: 0.1);
                  },
                ),
        ),
      ]),
    );
  }
}

class _Seg extends StatelessWidget {
  const _Seg({required this.label, required this.selected, required this.onTap});
  final String label;
  final bool selected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) => Pressable(
        onTap: onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 250),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 9),
          decoration: BoxDecoration(
            gradient: selected ? VColors.brand : null,
            color: selected ? null : Theme.of(context).hintColor.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(18),
          ),
          child: Text(label, style: TextStyle(fontWeight: FontWeight.w600, color: selected ? Colors.white : null)),
        ),
      );
}
