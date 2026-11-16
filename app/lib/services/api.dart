import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:http/http.dart' as http;

import 'backend.dart';

class ApiException implements Exception {
  ApiException(this.message);
  final String message;
  @override
  String toString() => message;
}

/// Voice + AI server se baat karta hai.
class Api {
  Api(this.backend);
  final Backend backend;

  String get base {
    final u = backend.config.serverUrl.trim();
    return u.endsWith('/') ? u.substring(0, u.length - 1) : u;
  }

  bool get configured => base.isNotEmpty;

  Future<Map<String, String>> _headers({bool json = true}) async {
    final t = await backend.idToken();
    return {
      if (json) 'Content-Type': 'application/json',
      if (t != null) 'Authorization': 'Bearer $t',
    };
  }

  void _check() {
    if (!configured) {
      throw ApiException('Voice server abhi set nahi hai. Owner Admin panel mein Server URL daalein.');
    }
  }

  static const offlineMsg = 'Sagar ki awaaz wala server abhi band hai (PC off hai). Thodi der baad try karein.';

  /// Internet / server band hone ki galti ko seedhi bhasha mein badlo.
  Future<T> _guard<T>(Future<T> Function() f) async {
    try {
      return await f();
    } on ApiException {
      rethrow;
    } on TimeoutException {
      throw ApiException('Server ne time pe jawab nahi diya. Dobara try karein.');
    } on SocketException {
      throw ApiException(offlineMsg);
    } on http.ClientException {
      throw ApiException(offlineMsg);
    } on HandshakeException {
      throw ApiException(offlineMsg);
    }
  }

  String _err(http.Response r) {
    try {
      final d = jsonDecode(utf8.decode(r.bodyBytes));
      if (d is Map && d['detail'] != null) return d['detail'].toString();
    } catch (_) {}
    if (r.statusCode == 530 || r.statusCode == 1033 || r.statusCode == 404) return offlineMsg;
    if (r.statusCode == 524) return 'Awaaz banne mein zyada time laga. Dobara try karein.';
    if (r.statusCode == 503 || r.statusCode == 502) return 'Server abhi jaag raha hai, 1 minute baad try karein';
    return 'Server error (${r.statusCode})';
  }

  Future<Uint8List> tts(String text, {String lang = 'auto'}) => _guard(() => _tts(text, lang: lang));

  Future<Uint8List> _tts(String text, {String lang = 'auto'}) async {
    _check();
    final r = await http
        .post(Uri.parse('$base/tts'), headers: await _headers(), body: jsonEncode({'text': text, 'lang': lang}))
        .timeout(const Duration(minutes: 4));
    if (r.statusCode != 200) throw ApiException(_err(r));
    return r.bodyBytes;
  }

  Future<String> ocr(List<File> files) => _guard(() => _ocr(files));

  Future<String> _ocr(List<File> files) async {
    _check();
    final req = http.MultipartRequest('POST', Uri.parse('$base/ocr'))..headers.addAll(await _headers(json: false));
    for (final f in files) {
      req.files.add(await http.MultipartFile.fromPath('files', f.path));
    }
    final res = await http.Response.fromStream(await req.send().timeout(const Duration(minutes: 3)));
    if (res.statusCode != 200) throw ApiException(_err(res));
    return (jsonDecode(utf8.decode(res.bodyBytes))['text'] ?? '').toString();
  }

  Future<String> ai(String action, String text, {String? question, String? targetLang, List<Map<String, String>>? history}) =>
      _guard(() => _ai(action, text, question: question, targetLang: targetLang, history: history));

  Future<String> _ai(String action, String text, {String? question, String? targetLang, List<Map<String, String>>? history}) async {
    _check();
    final r = await http
        .post(
          Uri.parse('$base/ai'),
          headers: await _headers(),
          body: jsonEncode({
            'action': action,
            'text': text,
            'question': question,
            'target_lang': targetLang,
            'history': history,
          }),
        )
        .timeout(const Duration(minutes: 2));
    if (r.statusCode != 200) throw ApiException(_err(r));
    return (jsonDecode(utf8.decode(r.bodyBytes))['text'] ?? '').toString();
  }

  Future<void> push(String title, String body) => _guard(() => _push(title, body));

  Future<void> _push(String title, String body) async {
    _check();
    final r = await http.post(Uri.parse('$base/admin/push'),
        headers: await _headers(), body: jsonEncode({'title': title, 'body': body}));
    if (r.statusCode != 200) throw ApiException(_err(r));
  }

  Future<Map<String, dynamic>> health() => _guard(_health);

  Future<Map<String, dynamic>> _health() async {
    _check();
    final r = await http.get(Uri.parse('$base/health')).timeout(const Duration(seconds: 60));
    if (r.statusCode != 200) throw ApiException(_err(r));
    return Map<String, dynamic>.from(jsonDecode(r.body));
  }
}
