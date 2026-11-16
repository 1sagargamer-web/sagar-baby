import 'dart:async';
import 'dart:convert';

import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:http/http.dart' as http;
import 'package:material_ui/material_ui.dart';
import 'package:package_info_plus/package_info_plus.dart';

import '../core/config.dart';

/// Owner (admin) dwara control hone wali settings. Firestore `config/app` doc
/// (ya GitHub JSON) ka format:
/// {
///   "maintenance": {"enabled": false, "title": "", "message": ""},
///   "notice": {"id": 0, "show": false, "title": "", "body": ""},
///   "update": {"latestVersion": 0, "minVersion": 0, "url": "", "note": ""},
///   "serverUrl": ""
/// }
class RemoteConfig {
  RemoteConfig(this.raw);
  final Map<String, dynamic> raw;

  Map<String, dynamic> _m(String k) => Map<String, dynamic>.from(raw[k] as Map? ?? {});
  static int _i(dynamic v) => v is num ? v.toInt() : int.tryParse('$v') ?? 0;

  bool get maintenance => _m('maintenance')['enabled'] == true;
  String get maintenanceTitle => (_m('maintenance')['title'] ?? '').toString();
  String get maintenanceMessage => (_m('maintenance')['message'] ?? '').toString();

  int get noticeId => _i(_m('notice')['id']);
  bool get noticeShow => _m('notice')['show'] == true;
  String get noticeTitle => (_m('notice')['title'] ?? '').toString();
  String get noticeBody => (_m('notice')['body'] ?? '').toString();

  int get latestVersion => _i(_m('update')['latestVersion']);
  int get minVersion => _i(_m('update')['minVersion']);
  String get updateUrl {
    final u = (_m('update')['url'] ?? '').toString().trim();
    return u.isEmpty ? AppConfig.defaultUpdateUrl : u;
  }

  String get updateNote => (_m('update')['note'] ?? '').toString();

  String get serverUrl {
    final u = (raw['serverUrl'] ?? '').toString().trim();
    return u.isEmpty ? AppConfig.defaultServerUrl : u;
  }
}

class Backend extends ChangeNotifier {
  bool firebaseOn = false;
  bool ready = false;
  User? user;
  String name = '';
  bool isAdmin = false;
  bool blocked = false;
  RemoteConfig config = RemoteConfig({});
  int buildNumber = 0;
  String version = '';

  StreamSubscription? _cfgSub, _authSub, _userSub;
  FirebaseFirestore get db => FirebaseFirestore.instance;

  bool get needsLogin => firebaseOn && user == null;
  bool get forceUpdate => config.minVersion > 0 && buildNumber < config.minVersion;
  bool get updateAvailable => config.latestVersion > buildNumber;

  Future<void> init() async {
    try {
      final info = await PackageInfo.fromPlatform();
      buildNumber = int.tryParse(info.buildNumber) ?? 0;
      version = info.version;
    } catch (_) {}

    if (AppConfig.firebaseConfigured) {
      try {
        await Firebase.initializeApp(
          options: const FirebaseOptions(
            apiKey: AppConfig.fbApiKey,
            appId: AppConfig.fbAppId,
            messagingSenderId: AppConfig.fbSenderId,
            projectId: AppConfig.fbProjectId,
            storageBucket: AppConfig.fbStorageBucket,
          ),
        );
        firebaseOn = true;
      } catch (e) {
        debugPrint('firebase init failed: $e');
      }
    }

    if (firebaseOn) {
      _cfgSub = db.doc('config/app').snapshots().listen((s) {
        config = RemoteConfig(s.data() ?? {});
        notifyListeners();
      }, onError: (e) => debugPrint('config error: $e'));
      final first = Completer<void>();
      _authSub = FirebaseAuth.instance.authStateChanges().listen((u) async {
        user = u;
        await _onUser(u);
        if (!first.isCompleted) first.complete();
        notifyListeners();
      });
      await first.future.timeout(const Duration(seconds: 6), onTimeout: () {});
      _setupPush();
    } else {
      await refreshGithubConfig();
    }
    ready = true;
    notifyListeners();
  }

  /// Firebase na ho to GitHub JSON se control.
  Future<void> refreshGithubConfig() async {
    if (firebaseOn) return;
    try {
      final r = await http
          .get(Uri.parse('${AppConfig.githubConfigUrl}?t=${DateTime.now().millisecondsSinceEpoch}'))
          .timeout(const Duration(seconds: 8));
      if (r.statusCode == 200) {
        config = RemoteConfig(Map<String, dynamic>.from(jsonDecode(r.body)));
        notifyListeners();
      }
    } catch (_) {}
  }

  Future<void> _onUser(User? u) async {
    await _userSub?.cancel();
    isAdmin = false;
    blocked = false;
    if (u == null) return;
    name = u.displayName ?? u.email?.split('@').first ?? 'Dost';
    try {
      final ref = db.doc('users/${u.uid}');
      final snap = await ref.get();
      await ref.set({
        'name': name,
        'email': u.email,
        'lastActive': FieldValue.serverTimestamp(),
        'appVersion': '$version+$buildNumber',
        if (!snap.exists) 'createdAt': FieldValue.serverTimestamp(),
        if (!snap.exists) 'blocked': false,
      }, SetOptions(merge: true));
      _userSub = ref.snapshots().listen((s) {
        final d = s.data() ?? {};
        blocked = d['blocked'] == true;
        if ((d['name'] ?? '').toString().isNotEmpty) name = d['name'];
        notifyListeners();
      });
      isAdmin = (await db.doc('admins/${u.uid}').get()).exists;
    } catch (e) {
      debugPrint('user doc failed: $e');
    }
  }

  Future<void> _setupPush() async {
    try {
      final m = FirebaseMessaging.instance;
      await m.requestPermission();
      await m.subscribeToTopic('all');
    } catch (e) {
      debugPrint('push setup failed: $e');
    }
  }

  // ---------------------------------------------------------------- Auth
  Future<void> signUp(String name, String email, String pass) async {
    final c = await FirebaseAuth.instance.createUserWithEmailAndPassword(email: email.trim(), password: pass);
    await c.user?.updateDisplayName(name.trim());
    this.name = name.trim();
    await db.doc('users/${c.user!.uid}').set({'name': name.trim()}, SetOptions(merge: true));
    notifyListeners();
  }

  Future<void> signIn(String email, String pass) =>
      FirebaseAuth.instance.signInWithEmailAndPassword(email: email.trim(), password: pass);

  Future<void> resetPassword(String email) => FirebaseAuth.instance.sendPasswordResetEmail(email: email.trim());

  Future<void> signOut() => FirebaseAuth.instance.signOut();

  Future<String?> idToken() async {
    if (!firebaseOn || user == null) return null;
    try {
      return await user!.getIdToken();
    } catch (_) {
      return null;
    }
  }

  // ---------------------------------------------------------------- Activity
  /// Owner ko dikhta hai kaun kya kar raha hai.
  void log(String action, [String detail = '']) {
    if (!firebaseOn || user == null) return;
    final d = detail.length > 300 ? '${detail.substring(0, 300)}…' : detail;
    db.collection('activity').add({
      'uid': user!.uid,
      'name': name,
      'action': action,
      'detail': d,
      'ts': FieldValue.serverTimestamp(),
    }).ignore();
    db.doc('users/${user!.uid}').set({
      'lastActive': FieldValue.serverTimestamp(),
      'stats': {action: FieldValue.increment(1)},
    }, SetOptions(merge: true)).ignore();
  }

  // ---------------------------------------------------------------- Admin
  Future<void> saveConfig(Map<String, dynamic> patch) =>
      db.doc('config/app').set(patch, SetOptions(merge: true));

  Stream<QuerySnapshot<Map<String, dynamic>>> usersStream() =>
      db.collection('users').orderBy('lastActive', descending: true).limit(300).snapshots();

  Stream<QuerySnapshot<Map<String, dynamic>>> activityStream() =>
      db.collection('activity').orderBy('ts', descending: true).limit(150).snapshots();

  Future<void> setBlocked(String uid, bool v) => db.doc('users/$uid').set({'blocked': v}, SetOptions(merge: true));

  @override
  void dispose() {
    _cfgSub?.cancel();
    _authSub?.cancel();
    _userSub?.cancel();
    super.dispose();
  }
}
