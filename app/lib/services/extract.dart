import 'dart:io';

import 'package:flutter/foundation.dart';
import 'package:google_mlkit_text_recognition/google_mlkit_text_recognition.dart';
import 'package:html/parser.dart' as html;
import 'package:http/http.dart' as http;
import 'package:syncfusion_flutter_pdf/pdf.dart';

import 'api.dart';

/// Photo / PDF / Link se text nikalna.
class Extractor {
  Extractor(this.api);
  final Api api;

  /// Photos (camera ya gallery). Pehle AI OCR (handwriting + Hindi best),
  /// server na mile to phone ka on-device OCR.
  Future<String> fromImages(List<File> images) async {
    if (api.configured) {
      try {
        final t = await api.ocr(images);
        if (t.trim().isNotEmpty) return t.trim();
      } catch (e) {
        debugPrint('server OCR failed, using on-device: $e');
      }
    }
    return _onDevice(images);
  }

  Future<String> _onDevice(List<File> images) async {
    final out = StringBuffer();
    final dev = TextRecognizer(script: TextRecognitionScript.devanagiri);
    final lat = TextRecognizer(script: TextRecognitionScript.latin);
    try {
      for (final f in images) {
        final input = InputImage.fromFile(f);
        final a = await dev.processImage(input);
        final b = await lat.processImage(input);
        // Jisme zyada text mila, wahi lo (Devanagari model English bhi padh leta hai)
        final best = a.text.length >= b.text.length * 0.9 ? a.text : b.text;
        if (best.trim().isNotEmpty) out.writeln('${best.trim()}\n');
      }
    } finally {
      await dev.close();
      await lat.close();
    }
    return out.toString().trim();
  }

  Future<String> fromPdf(File file) async {
    String text = '';
    try {
      final bytes = await file.readAsBytes();
      text = await compute(_pdfText, bytes);
    } catch (e) {
      debugPrint('pdf text failed: $e');
    }
    // Scanned PDF (photo wali) -> AI se padhwao
    if (text.replaceAll(RegExp(r'\s'), '').length < 30) {
      if (!api.configured) {
        throw ApiException('Ye scanned PDF hai. Isko padhne ke liye voice server chahiye.');
      }
      text = await api.ocr([file]);
    }
    return text.trim();
  }

  Future<String> fromLink(String url) async {
    var u = url.trim();
    if (!u.startsWith('http')) u = 'https://$u';
    final r = await http.get(Uri.parse(u), headers: {'User-Agent': 'Mozilla/5.0 (Android) SagarVaani'}).timeout(const Duration(seconds: 20));
    if (r.statusCode != 200) throw ApiException('Page open nahi hua (${r.statusCode})');
    final doc = html.parse(r.body);
    doc.querySelectorAll('script,style,noscript,nav,footer,header,aside,form,svg').forEach((e) => e.remove());
    final root = doc.querySelector('article') ?? doc.querySelector('main') ?? doc.body;
    final blocks = <String>[];
    for (final e in root?.querySelectorAll('h1,h2,h3,p,li,blockquote') ?? []) {
      final t = e.text.replaceAll(RegExp(r'\s+'), ' ').trim();
      if (t.length > 1) blocks.add(t);
    }
    var text = blocks.join('\n\n');
    if (text.length < 80) text = (root?.text ?? '').replaceAll(RegExp(r'\s+'), ' ').trim();
    if (text.isEmpty) throw ApiException('Is page pe padhne layak text nahi mila');
    return text;
  }
}

String _pdfText(List<int> bytes) {
  final doc = PdfDocument(inputBytes: bytes);
  try {
    return PdfTextExtractor(doc).extractText();
  } finally {
    doc.dispose();
  }
}
