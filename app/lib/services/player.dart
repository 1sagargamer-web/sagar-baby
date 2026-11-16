import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:just_audio/just_audio.dart';
import 'package:just_audio_background/just_audio_background.dart';
import 'package:material_ui/material_ui.dart';
import 'package:path_provider/path_provider.dart';

import 'api.dart';

enum VoiceState { idle, loading, playing, paused, waiting, done, error }

/// Text ko chhote hisson mein bolta hai (pehla hissa aate hi bolna shuru),
/// background + lock screen pe bhi chalta rehta hai.
class VoicePlayer extends ChangeNotifier {
  VoicePlayer(this.api) {
    _player.playerStateStream.listen(_onPlayerState);
    _player.currentIndexStream.listen((i) {
      if (i != null && i != _index) {
        _index = i;
        _prefetch();
        notifyListeners();
      }
    });
    _player.positionStream.listen((_) => notifyListeners());
  }

  final Api api;
  final AudioPlayer _player = AudioPlayer();

  VoiceState state = VoiceState.idle;
  String? error;
  String title = '';
  String _fullText = '';
  List<String> chunks = [];
  final Map<int, File> _files = {};
  final Set<int> _fetching = {};
  int _added = 0; // playlist mein kitne hisse daale
  int _index = 0;
  int _session = 0;
  double speed = 1.0;

  int get index => _index;
  bool get isPlaying => state == VoiceState.playing || state == VoiceState.waiting;
  bool get hasContent => chunks.isNotEmpty;
  String get currentText => _fullText;

  double get progress {
    if (chunks.isEmpty) return 0;
    final d = _player.duration?.inMilliseconds ?? 0;
    final p = _player.position.inMilliseconds;
    final part = d > 0 ? (p / d).clamp(0.0, 1.0) : 0.0;
    return ((_index + part) / chunks.length).clamp(0.0, 1.0);
  }

  /// Naya text bolna shuru karo.
  Future<void> speak(String text, {String title = 'Sagar Vaani', String lang = 'auto'}) async {
    final clean = text.trim();
    if (clean.isEmpty) return;
    _session++;
    final my = _session;
    await _player.stop();
    this.title = title;
    _fullText = clean;
    _lang = lang;
    chunks = splitText(clean);
    _files.clear();
    _fetching.clear();
    _added = 0;
    _index = 0;
    error = null;
    state = VoiceState.loading;
    notifyListeners();
    try {
      final f0 = await _get(0, my);
      if (my != _session || f0 == null) return;
      await _player.setAudioSources([_source(0, f0)], initialIndex: 0, initialPosition: Duration.zero);
      _added = 1;
      await _player.setSpeed(speed);
      _player.play();
      _prefetch();
    } catch (e) {
      if (my != _session) return;
      state = VoiceState.error;
      error = e is ApiException ? e.message : 'Awaaz nahi ban payi. Internet / server check karein.';
      notifyListeners();
    }
  }

  String _lang = 'auto';

  AudioSource _source(int i, File f) => AudioSource.file(
        f.path,
        tag: MediaItem(
          id: '${_session}_$i',
          title: title,
          album: 'Sagar Vaani',
          artist: 'Sagar ki awaaz • Part ${i + 1}/${chunks.length}',
        ),
      );

  Future<File?> _get(int i, int my) async {
    if (_files[i] != null) return _files[i];
    final dir = await getTemporaryDirectory();
    final key = cacheKey(chunks[i], _lang);
    final f = File('${dir.path}/vaani_$key.mp3');
    if (await f.exists() && await f.length() > 0) {
      _files[i] = f;
      return f;
    }
    final bytes = await api.tts(chunks[i], lang: _lang);
    if (my != _session) return null;
    await f.writeAsBytes(bytes, flush: true);
    _files[i] = f;
    return f;
  }

  /// Aage ke 2 hisse pehle se bana ke rakho, taaki rukna na pade.
  Future<void> _prefetch() async {
    final my = _session;
    for (var i = _added; i < chunks.length && i <= _index + 2; i++) {
      if (_fetching.contains(i)) return;
      _fetching.add(i);
      try {
        final f = await _get(i, my);
        if (my != _session || f == null) return;
        // order mein hi add karo
        if (i == _added) {
          await _player.addAudioSource(_source(i, f));
          _added++;
          if (state == VoiceState.waiting) {
            await _player.seek(Duration.zero, index: _added - 1);
            _player.play();
          }
        }
      } catch (e) {
        if (my != _session) return;
        if (state == VoiceState.waiting) {
          state = VoiceState.error;
          error = e is ApiException ? e.message : 'Agla hissa load nahi hua';
          notifyListeners();
        }
        return;
      } finally {
        _fetching.remove(i);
      }
    }
  }

  void _onPlayerState(PlayerState s) {
    if (chunks.isEmpty) return;
    if (s.processingState == ProcessingState.completed) {
      if (_added < chunks.length) {
        state = VoiceState.waiting; // agla hissa ban raha hai
        _prefetch();
      } else {
        state = VoiceState.done;
      }
    } else if (s.processingState == ProcessingState.loading || s.processingState == ProcessingState.buffering) {
      if (state != VoiceState.waiting) state = s.playing ? VoiceState.playing : state;
    } else if (s.playing) {
      state = VoiceState.playing;
    } else if (state == VoiceState.playing) {
      state = VoiceState.paused;
    }
    notifyListeners();
  }

  Future<void> toggle() async {
    if (state == VoiceState.playing || state == VoiceState.waiting) {
      await _player.pause();
      state = VoiceState.paused;
    } else if (state == VoiceState.paused) {
      _player.play();
    } else if (state == VoiceState.done) {
      await _player.seek(Duration.zero, index: 0);
      _player.play();
    } else if ((state == VoiceState.error || state == VoiceState.idle) && _fullText.isNotEmpty) {
      await speak(_fullText, title: title, lang: _lang);
      return;
    }
    notifyListeners();
  }

  Future<void> next() async {
    if (_index + 1 < _added) await _player.seek(Duration.zero, index: _index + 1);
  }

  Future<void> previous() async {
    if (_player.position.inSeconds > 2 || _index == 0) {
      await _player.seek(Duration.zero);
    } else {
      await _player.seek(Duration.zero, index: _index - 1);
    }
  }

  Future<void> setSpeed(double v) async {
    speed = v;
    await _player.setSpeed(v);
    notifyListeners();
  }

  Future<void> stop() async {
    _session++;
    await _player.stop();
    chunks = [];
    _fullText = '';
    state = VoiceState.idle;
    notifyListeners();
  }

  /// Poora text ek MP3 file mein (download / WhatsApp share ke liye).
  Future<File> exportMp3(String text, String name, {String lang = 'auto', void Function(double)? onProgress}) async {
    final parts = splitText(text);
    final dir = await getTemporaryDirectory();
    final out = BytesBuilder(copy: false);
    for (var i = 0; i < parts.length; i++) {
      final key = cacheKey(parts[i], lang);
      final cache = File('${dir.path}/vaani_$key.mp3');
      Uint8List b;
      if (await cache.exists() && await cache.length() > 0) {
        b = await cache.readAsBytes();
      } else {
        b = await api.tts(parts[i], lang: lang);
        await cache.writeAsBytes(b);
      }
      out.add(b);
      onProgress?.call((i + 1) / parts.length);
    }
    final safe = name.replaceAll(RegExp(r'[^\wऀ-ॿ ]+'), '').trim();
    final f = File('${dir.path}/SagarVaani_${safe.isEmpty ? 'audio' : safe.substring(0, safe.length.clamp(0, 30))}.mp3');
    await f.writeAsBytes(out.takeBytes(), flush: true);
    return f;
  }

  /// Har baar same rehne wala chhota hash (FNV-1a), audio cache ke liye.
  static String cacheKey(String text, String lang) {
    var h = 0x811c9dc5;
    for (final b in utf8.encode('$lang|$text')) {
      h = ((h ^ b) * 0x01000193) & 0xFFFFFFFF;
    }
    return '${h.toRadixString(16)}_${text.length}_$lang';
  }

  /// Text ko vakyon ke hisaab se ~320 akshar ke tukdon mein todo.
  /// Pehla tukda chhota (jaldi bolna shuru ho), baaki ~220 akshar
  /// (har tukda ~100 second ke andar ban jaye, internet link ki limit).
  static List<String> splitText(String text, {int limit = 220, int firstLimit = 140}) {
    final t = text.replaceAll(RegExp(r'[ \t]+'), ' ').replaceAll(RegExp(r'\n{2,}'), '\n').trim();
    final sentences = t.split(RegExp(r'(?<=[.!?।॥\n])\s+'));
    final out = <String>[];
    var cur = '';
    for (var s in sentences) {
      s = s.trim();
      if (s.isEmpty) continue;
      final lim = out.isEmpty ? firstLimit : limit;
      while (s.length > lim) {
        var cut = s.lastIndexOf(RegExp(r'[,\s]'), lim);
        if (cut < 60) cut = lim;
        if (cur.isNotEmpty) {
          out.add(cur);
          cur = '';
        }
        out.add(s.substring(0, cut).trim());
        s = s.substring(cut).trim();
      }
      if (cur.length + s.length + 1 <= (out.isEmpty ? firstLimit : limit)) {
        cur = cur.isEmpty ? s : '$cur $s';
      } else {
        if (cur.isNotEmpty) out.add(cur);
        cur = s;
      }
    }
    if (cur.isNotEmpty) out.add(cur);
    return out;
  }

  @override
  void dispose() {
    _player.dispose();
    super.dispose();
  }
}
