import 'dart:convert';
import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:path_provider/path_provider.dart';

/// Ek padha gaya page / document.
class VaaniDoc {
  VaaniDoc({
    required this.id,
    required this.title,
    required this.text,
    required this.source,
    required this.createdAt,
    DateTime? openedAt,
    this.bookmarked = false,
    this.summary,
    this.translation,
  }) : openedAt = openedAt ?? createdAt;

  final String id;
  String title;
  String text;
  final String source; // camera | photo | pdf | text | link
  final DateTime createdAt;
  DateTime openedAt;
  bool bookmarked;
  String? summary;
  String? translation;

  int get words => text.trim().isEmpty ? 0 : text.trim().split(RegExp(r'\s+')).length;

  Map<String, dynamic> toJson() => {
        'id': id,
        'title': title,
        'text': text,
        'source': source,
        'createdAt': createdAt.toIso8601String(),
        'openedAt': openedAt.toIso8601String(),
        'bookmarked': bookmarked,
        'summary': summary,
        'translation': translation,
      };

  factory VaaniDoc.fromJson(Map<String, dynamic> j) => VaaniDoc(
        id: j['id'],
        title: j['title'] ?? 'Page',
        text: j['text'] ?? '',
        source: j['source'] ?? 'text',
        createdAt: DateTime.tryParse(j['createdAt'] ?? '') ?? DateTime.now(),
        openedAt: DateTime.tryParse(j['openedAt'] ?? ''),
        bookmarked: j['bookmarked'] == true,
        summary: j['summary'],
        translation: j['translation'],
      );

  static String makeTitle(String text) {
    final t = text.trim().replaceAll(RegExp(r'\s+'), ' ');
    if (t.isEmpty) return 'Naya page';
    return t.length > 42 ? '${t.substring(0, 42)}…' : t;
  }
}

/// Library + History - phone mein hi save rehti hai.
class LibraryStore extends ChangeNotifier {
  final List<VaaniDoc> _docs = [];
  File? _file;

  List<VaaniDoc> get all => List.unmodifiable(_docs..sort((a, b) => b.openedAt.compareTo(a.openedAt)));
  List<VaaniDoc> get bookmarks => all.where((d) => d.bookmarked).toList();

  Future<void> load() async {
    try {
      final dir = await getApplicationDocumentsDirectory();
      _file = File('${dir.path}/library.json');
      if (await _file!.exists()) {
        final list = jsonDecode(await _file!.readAsString()) as List;
        _docs
          ..clear()
          ..addAll(list.map((e) => VaaniDoc.fromJson(Map<String, dynamic>.from(e))));
      }
    } catch (e) {
      debugPrint('library load failed: $e');
    }
    notifyListeners();
  }

  Future<void> _save() async {
    try {
      await _file?.writeAsString(jsonEncode(_docs.map((d) => d.toJson()).toList()));
    } catch (e) {
      debugPrint('library save failed: $e');
    }
  }

  VaaniDoc create(String text, String source, {String? title}) {
    final d = VaaniDoc(
      id: DateTime.now().microsecondsSinceEpoch.toString(),
      title: title ?? VaaniDoc.makeTitle(text),
      text: text,
      source: source,
      createdAt: DateTime.now(),
    );
    _docs.add(d);
    _save();
    notifyListeners();
    return d;
  }

  void touch(VaaniDoc d) {
    d.openedAt = DateTime.now();
    update(d);
  }

  void update(VaaniDoc d) {
    _save();
    notifyListeners();
  }

  void toggleBookmark(VaaniDoc d) {
    d.bookmarked = !d.bookmarked;
    update(d);
  }

  void remove(VaaniDoc d) {
    _docs.removeWhere((x) => x.id == d.id);
    _save();
    notifyListeners();
  }

  void clearHistory() {
    _docs.removeWhere((d) => !d.bookmarked);
    _save();
    notifyListeners();
  }
}
