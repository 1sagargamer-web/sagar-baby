import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:material_ui/material_ui.dart';
import 'package:provider/provider.dart';

import '../core/theme.dart';
import '../services/api.dart';
import '../services/backend.dart';
import '../widgets/common.dart';
import 'home_shell.dart' show ago;

/// Owner panel: kaun app use kar raha hai, kya kar raha hai, aur poora control.
class AdminScreen extends StatefulWidget {
  const AdminScreen({super.key});

  @override
  State<AdminScreen> createState() => _AdminScreenState();
}

class _AdminScreenState extends State<AdminScreen> {
  int _tab = 0;

  @override
  Widget build(BuildContext context) {
    const tabs = ['Dashboard', 'Users', 'Activity', 'Control'];
    return SafeArea(
      bottom: false,
      child: Column(children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(18, 10, 18, 8),
          child: Row(children: [
            const IconBubble(icon: Icons.admin_panel_settings_rounded, size: 44, gradient: VColors.warm),
            const SizedBox(width: 12),
            const Expanded(child: Text('Owner Panel', style: TextStyle(fontSize: 26, fontWeight: FontWeight.w800))),
          ]),
        ),
        SizedBox(
          height: 46,
          child: ListView(
            scrollDirection: Axis.horizontal,
            padding: const EdgeInsets.symmetric(horizontal: 18),
            children: [
              for (var i = 0; i < tabs.length; i++)
                Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: Pressable(
                    onTap: () => setState(() => _tab = i),
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 250),
                      padding: const EdgeInsets.symmetric(horizontal: 18),
                      alignment: Alignment.center,
                      decoration: BoxDecoration(
                        gradient: _tab == i ? VColors.brand : null,
                        color: _tab == i ? null : Theme.of(context).hintColor.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(18),
                      ),
                      child: Text(tabs[i], style: TextStyle(fontWeight: FontWeight.w600, color: _tab == i ? Colors.white : null)),
                    ),
                  ),
                ),
            ],
          ),
        ),
        Expanded(
          child: AnimatedSwitcher(
            duration: const Duration(milliseconds: 250),
            child: KeyedSubtree(
              key: ValueKey(_tab),
              child: switch (_tab) {
                0 => const _Dashboard(),
                1 => const _Users(),
                2 => const _Activity(),
                _ => const _Control(),
              },
            ),
          ),
        ),
      ]),
    );
  }
}

DateTime? _ts(dynamic v) => v is Timestamp ? v.toDate() : null;

String actionLabel(String a) => switch (a) {
      'page_camera' => '📷 Camera se scan kiya',
      'page_photo' => '🖼️ Photo daali',
      'page_pdf' => '📄 PDF khola',
      'page_text' => '📝 Text daala',
      'page_link' => '🌐 Web page khola',
      'read_page' => '🔊 Poora page suna',
      'read_selected' => '🔉 Selected text suna',
      'summary' => '📌 Saar banaya',
      'translate' => '🌍 Translate kiya',
      'ask_ai' => '🤖 AI se poocha',
      'download_mp3' => '⬇️ MP3 download kiya',
      _ => a,
    };

class _Dashboard extends StatelessWidget {
  const _Dashboard();

  @override
  Widget build(BuildContext context) {
    final b = context.read<Backend>();
    return StreamBuilder<QuerySnapshot<Map<String, dynamic>>>(
      stream: b.usersStream(),
      builder: (_, snap) {
        final users = snap.data?.docs ?? [];
        final now = DateTime.now();
        final today = DateTime(now.year, now.month, now.day);
        final activeToday = users.where((u) => (_ts(u.data()['lastActive']) ?? DateTime(2000)).isAfter(today)).length;
        final active7 = users.where((u) => (_ts(u.data()['lastActive']) ?? DateTime(2000)).isAfter(now.subtract(const Duration(days: 7)))).length;
        final blocked = users.where((u) => u.data()['blocked'] == true).length;
        final totals = <String, int>{};
        for (final u in users) {
          final st = Map<String, dynamic>.from(u.data()['stats'] as Map? ?? {});
          st.forEach((k, v) => totals[k] = (totals[k] ?? 0) + ((v as num?)?.toInt() ?? 0));
        }
        final newToday = users.where((u) => (_ts(u.data()['createdAt']) ?? DateTime(2000)).isAfter(today)).length;

        return ListView(padding: const EdgeInsets.fromLTRB(18, 14, 18, 190), children: [
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
            childAspectRatio: 1.5,
            children: [
              _Stat('Total Users', '${users.length}', Icons.groups_rounded, VColors.brand),
              _Stat('Aaj Active', '$activeToday', Icons.bolt_rounded, const LinearGradient(colors: [Color(0xFF25D366), Color(0xFF128C7E)])),
              _Stat('7 din Active', '$active7', Icons.trending_up_rounded, const LinearGradient(colors: [Color(0xFF8B5CF6), Color(0xFFEC4899)])),
              _Stat('Aaj Naye', '$newToday', Icons.person_add_alt_1_rounded, VColors.warm),
            ],
          ),
          if (blocked > 0) Padding(padding: const EdgeInsets.only(top: 10), child: Text('🚫 Blocked users: $blocked')),
          const SectionTitle('Kya sabse zyada use ho raha hai'),
          Glass(
            child: totals.isEmpty
                ? const Text('Abhi koi data nahi')
                : Column(children: [
                    for (final e in (totals.entries.toList()..sort((a, c) => c.value.compareTo(a.value))))
                      Padding(
                        padding: const EdgeInsets.symmetric(vertical: 6),
                        child: Row(children: [
                          Expanded(child: Text(actionLabel(e.key))),
                          Text('${e.value}', style: const TextStyle(fontWeight: FontWeight.w800)),
                        ]),
                      ),
                  ]),
          ),
          const SectionTitle('Voice Server'),
          const _ServerHealth(),
        ]);
      },
    );
  }
}

class _Stat extends StatelessWidget {
  const _Stat(this.label, this.value, this.icon, this.gradient);
  final String label, value;
  final IconData icon;
  final Gradient gradient;

  @override
  Widget build(BuildContext context) => Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(gradient: gradient, borderRadius: BorderRadius.circular(22)),
        child: Column(crossAxisAlignment: CrossAxisAlignment.start, mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          Icon(icon, color: Colors.white),
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(value, style: const TextStyle(color: Colors.white, fontSize: 26, fontWeight: FontWeight.w800)),
            Text(label, style: TextStyle(color: Colors.white.withValues(alpha: 0.9), fontSize: 12)),
          ]),
        ]),
      );
}

class _ServerHealth extends StatefulWidget {
  const _ServerHealth();

  @override
  State<_ServerHealth> createState() => _ServerHealthState();
}

class _ServerHealthState extends State<_ServerHealth> {
  Map<String, dynamic>? _h;
  String? _err;
  bool _loading = false;

  Future<void> _check() async {
    setState(() {
      _loading = true;
      _err = null;
    });
    try {
      _h = await context.read<Api>().health();
    } catch (e) {
      _err = e.toString();
      _h = null;
    }
    if (mounted) setState(() => _loading = false);
  }

  @override
  Widget build(BuildContext context) {
    Widget row(String t, bool ok) => Padding(
          padding: const EdgeInsets.symmetric(vertical: 3),
          child: Row(children: [
            Icon(ok ? Icons.check_circle_rounded : Icons.cancel_rounded, color: ok ? const Color(0xFF25D366) : VColors.coral, size: 20),
            const SizedBox(width: 8),
            Text(t),
          ]),
        );
    return Glass(
      child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
        Text(context.read<Api>().base.isEmpty ? 'Server URL set nahi hai (Control tab mein daalo)' : context.read<Api>().base,
            style: TextStyle(fontSize: 12, color: Theme.of(context).hintColor)),
        const SizedBox(height: 10),
        if (_h != null) ...[
          row('Server chal raha hai', _h!['ok'] == true),
          row('Aapki voice sample mili', _h!['voice_sample'] == true),
          row('Voice model ready', _h!['voice_loaded'] == true),
          row('AI (Gemini) key set', _h!['ai'] == true),
          row('Firebase (login check + push)', _h!['firebase'] == true),
        ],
        if (_err != null) Text(_err!, style: const TextStyle(color: VColors.coral)),
        const SizedBox(height: 10),
        GradientButton(label: 'Server check karo', icon: Icons.wifi_tethering_rounded, loading: _loading, onTap: _check, height: 48),
      ]),
    );
  }
}

class _Users extends StatefulWidget {
  const _Users();

  @override
  State<_Users> createState() => _UsersState();
}

class _UsersState extends State<_Users> {
  String _q = '';

  @override
  Widget build(BuildContext context) {
    final b = context.read<Backend>();
    return Column(children: [
      Padding(
        padding: const EdgeInsets.fromLTRB(18, 14, 18, 6),
        child: TextField(
          onChanged: (v) => setState(() => _q = v.toLowerCase()),
          decoration: const InputDecoration(hintText: 'Naam ya email se dhoondo', prefixIcon: Icon(Icons.search_rounded)),
        ),
      ),
      Expanded(
        child: StreamBuilder<QuerySnapshot<Map<String, dynamic>>>(
          stream: b.usersStream(),
          builder: (_, snap) {
            if (!snap.hasData) return const Center(child: CircularProgressIndicator());
            final users = snap.data!.docs.where((u) {
              final d = u.data();
              return _q.isEmpty || '${d['name']} ${d['email']}'.toLowerCase().contains(_q);
            }).toList();
            return ListView.builder(
              padding: const EdgeInsets.fromLTRB(18, 8, 18, 190),
              itemCount: users.length,
              itemBuilder: (_, i) {
                final u = users[i];
                final d = u.data();
                final blocked = d['blocked'] == true;
                final last = _ts(d['lastActive']);
                final stats = Map<String, dynamic>.from(d['stats'] as Map? ?? {});
                final total = stats.values.fold<int>(0, (a, v) => a + ((v as num?)?.toInt() ?? 0));
                return Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: Glass(
                    radius: 22,
                    padding: const EdgeInsets.all(14),
                    onTap: () => _detail(context, u.id, d),
                    child: Row(children: [
                      CircleAvatar(
                        backgroundColor: blocked ? VColors.coral : VColors.ocean,
                        child: Text(('${d['name'] ?? '?'}').characters.first.toUpperCase(), style: const TextStyle(color: Colors.white)),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                          Text('${d['name'] ?? '-'}${blocked ? '  🚫' : ''}', style: const TextStyle(fontWeight: FontWeight.w600)),
                          Text('${d['email'] ?? ''}', style: TextStyle(fontSize: 12, color: Theme.of(context).hintColor)),
                          Text('${last == null ? '-' : ago(last)} • $total kaam • v${d['appVersion'] ?? '?'}',
                              style: TextStyle(fontSize: 11.5, color: Theme.of(context).hintColor)),
                        ]),
                      ),
                      const Icon(Icons.chevron_right_rounded),
                    ]),
                  ),
                );
              },
            );
          },
        ),
      ),
    ]);
  }

  void _detail(BuildContext context, String uid, Map<String, dynamic> d) {
    final b = context.read<Backend>();
    final blocked = d['blocked'] == true;
    final stats = Map<String, dynamic>.from(d['stats'] as Map? ?? {});
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (c) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(22),
          child: Column(mainAxisSize: MainAxisSize.min, crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Text('${d['name'] ?? '-'}', style: const TextStyle(fontSize: 21, fontWeight: FontWeight.w800)),
            Text('${d['email'] ?? ''}', style: TextStyle(color: Theme.of(c).hintColor)),
            const SizedBox(height: 6),
            Text('Joined: ${_ts(d['createdAt'])?.toString().split('.').first ?? '-'}', style: const TextStyle(fontSize: 12)),
            Text('Last active: ${_ts(d['lastActive'])?.toString().split('.').first ?? '-'}', style: const TextStyle(fontSize: 12)),
            const SizedBox(height: 14),
            for (final e in stats.entries)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 3),
                child: Row(children: [Expanded(child: Text(actionLabel(e.key))), Text('${e.value}', style: const TextStyle(fontWeight: FontWeight.w700))]),
              ),
            const SizedBox(height: 20),
            GradientButton(
              label: blocked ? 'Unblock karo' : 'Block karo',
              icon: blocked ? Icons.lock_open_rounded : Icons.block_rounded,
              gradient: blocked ? VColors.brand : const LinearGradient(colors: [VColors.coral, Color(0xFFB91C1C)]),
              onTap: () async {
                Navigator.pop(c);
                await b.setBlocked(uid, !blocked);
                if (context.mounted) toast(context, blocked ? 'Unblock ho gaya' : 'Block ho gaya');
              },
            ),
          ]),
        ),
      ),
    );
  }
}

class _Activity extends StatelessWidget {
  const _Activity();

  @override
  Widget build(BuildContext context) {
    return StreamBuilder<QuerySnapshot<Map<String, dynamic>>>(
      stream: context.read<Backend>().activityStream(),
      builder: (_, snap) {
        if (!snap.hasData) return const Center(child: CircularProgressIndicator());
        final items = snap.data!.docs;
        if (items.isEmpty) return const Center(child: Text('Abhi koi activity nahi'));
        return ListView.builder(
          padding: const EdgeInsets.fromLTRB(18, 14, 18, 190),
          itemCount: items.length,
          itemBuilder: (_, i) {
            final d = items[i].data();
            final t = _ts(d['ts']);
            return Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: Glass(
                radius: 18,
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Row(children: [
                    Expanded(child: Text('${d['name'] ?? '-'}', style: const TextStyle(fontWeight: FontWeight.w700))),
                    Text(t == null ? '' : ago(t), style: TextStyle(fontSize: 11.5, color: Theme.of(context).hintColor)),
                  ]),
                  const SizedBox(height: 2),
                  Text(actionLabel('${d['action']}'), style: const TextStyle(fontSize: 13.5)),
                  if ('${d['detail'] ?? ''}'.isNotEmpty)
                    Text('"${d['detail']}"', maxLines: 3, overflow: TextOverflow.ellipsis, style: TextStyle(fontSize: 12.5, color: Theme.of(context).hintColor)),
                ]),
              ),
            );
          },
        );
      },
    );
  }
}

class _Control extends StatefulWidget {
  const _Control();

  @override
  State<_Control> createState() => _ControlState();
}

class _ControlState extends State<_Control> {
  late final RemoteConfig c = context.read<Backend>().config;
  late bool _maint = c.maintenance;
  late final _mTitle = TextEditingController(text: c.maintenanceTitle);
  late final _mMsg = TextEditingController(text: c.maintenanceMessage);
  final _nTitle = TextEditingController();
  final _nBody = TextEditingController();
  bool _push = true;
  late final _latest = TextEditingController(text: '${c.latestVersion}');
  late final _min = TextEditingController(text: '${c.minVersion}');
  late final _url = TextEditingController(text: (c.raw['update'] as Map?)?['url']?.toString() ?? '');
  late final _note = TextEditingController(text: c.updateNote);
  late final _server = TextEditingController(text: c.raw['serverUrl']?.toString() ?? '');
  bool _saving = false;

  Future<void> _save(String what, Map<String, dynamic> patch) async {
    setState(() => _saving = true);
    try {
      await context.read<Backend>().saveConfig(patch);
      if (mounted) toast(context, '$what save ho gaya ✓ Sab users ke paas pahunch gaya');
    } catch (e) {
      if (mounted) toast(context, 'Save nahi hua: $e');
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Future<void> _sendNotice() async {
    if (_nTitle.text.trim().isEmpty && _nBody.text.trim().isEmpty) return toast(context, 'Notice likho');
    final b = context.read<Backend>();
    final api = context.read<Api>();
    await _save('Notice', {
      'notice': {'id': DateTime.now().millisecondsSinceEpoch ~/ 1000, 'show': true, 'title': _nTitle.text.trim(), 'body': _nBody.text.trim()},
    });
    if (_push) {
      try {
        await api.push(_nTitle.text.trim().isEmpty ? 'Sagar Vaani' : _nTitle.text.trim(), _nBody.text.trim());
        if (mounted) toast(context, 'Notice + Push notification bhej diya 🔔');
      } catch (e) {
        if (mounted) toast(context, 'Notice app mein dikh jayega. Push nahi gaya: $e');
      }
    }
    b.log('admin_notice', _nTitle.text);
  }

  @override
  Widget build(BuildContext context) {
    final cfg = context.watch<Backend>().config;
    return ListView(padding: const EdgeInsets.fromLTRB(18, 14, 18, 190), children: [
      // -------------------------------------------------- maintenance
      _Card(
        icon: Icons.construction_rounded,
        title: 'Maintenance Mode',
        subtitle: 'On karte hi sabke liye app band (sirf aap chala paoge)',
        child: Column(children: [
          SwitchListTile(
            contentPadding: EdgeInsets.zero,
            value: _maint,
            title: Text(_maint ? 'ON - app band hai' : 'OFF - app chal raha hai', style: TextStyle(fontWeight: FontWeight.w700, color: _maint ? VColors.coral : null)),
            onChanged: (v) => setState(() => _maint = v),
          ),
          TextField(controller: _mTitle, decoration: const InputDecoration(hintText: 'Title (jaise: Update chal raha hai)')),
          const SizedBox(height: 10),
          TextField(controller: _mMsg, maxLines: 2, decoration: const InputDecoration(hintText: 'Message users ke liye')),
          const SizedBox(height: 12),
          GradientButton(
            label: 'Maintenance save karo',
            height: 48,
            loading: _saving,
            onTap: () => _save('Maintenance', {
              'maintenance': {'enabled': _maint, 'title': _mTitle.text.trim(), 'message': _mMsg.text.trim()},
            }),
          ),
        ]),
      ),

      // -------------------------------------------------- notice
      _Card(
        icon: Icons.campaign_rounded,
        title: 'Notice bhejo',
        subtitle: cfg.noticeShow ? 'Abhi chal raha: "${cfg.noticeTitle}"' : 'Sabke phone pe popup + notification',
        child: Column(children: [
          TextField(controller: _nTitle, decoration: const InputDecoration(hintText: 'Notice ka title')),
          const SizedBox(height: 10),
          TextField(controller: _nBody, maxLines: 3, decoration: const InputDecoration(hintText: 'Notice ka message')),
          CheckboxListTile(
            contentPadding: EdgeInsets.zero,
            value: _push,
            onChanged: (v) => setState(() => _push = v ?? true),
            title: const Text('Push notification bhi bhejo'),
          ),
          Row(children: [
            Expanded(child: GradientButton(label: 'Sabko bhejo', icon: Icons.send_rounded, height: 48, loading: _saving, onTap: _sendNotice)),
            const SizedBox(width: 10),
            if (cfg.noticeShow)
              TextButton(
                onPressed: () => _save('Notice hatana', {
                  'notice': {...Map<String, dynamic>.from(cfg.raw['notice'] as Map? ?? {}), 'show': false},
                }),
                child: const Text('Notice hatao'),
              ),
          ]),
        ]),
      ),

      // -------------------------------------------------- update
      _Card(
        icon: Icons.system_update_rounded,
        title: 'App Update',
        subtitle: 'Abhi aapka build: ${context.read<Backend>().buildNumber}. Naya APK GitHub Release pe banta hai.',
        child: Column(children: [
          Row(children: [
            Expanded(child: TextField(controller: _latest, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Latest build no.'))),
            const SizedBox(width: 10),
            Expanded(child: TextField(controller: _min, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Force (min) build'))),
          ]),
          const SizedBox(height: 10),
          TextField(controller: _url, decoration: const InputDecoration(hintText: 'Update link (khaali = GitHub latest APK)')),
          const SizedBox(height: 10),
          TextField(controller: _note, maxLines: 2, decoration: const InputDecoration(hintText: 'Update note (kya naya hai)')),
          const SizedBox(height: 6),
          Text('Latest > user ka build → "Update aaya" banner. Force > user ka build → bina update app nahi chalega.',
              style: TextStyle(fontSize: 11.5, color: Theme.of(context).hintColor)),
          const SizedBox(height: 12),
          GradientButton(
            label: 'Update info save karo',
            height: 48,
            loading: _saving,
            onTap: () => _save('Update', {
              'update': {
                'latestVersion': int.tryParse(_latest.text.trim()) ?? 0,
                'minVersion': int.tryParse(_min.text.trim()) ?? 0,
                'url': _url.text.trim(),
                'note': _note.text.trim(),
              },
            }),
          ),
        ]),
      ),

      // -------------------------------------------------- server
      _Card(
        icon: Icons.dns_rounded,
        title: 'Voice Server URL',
        subtitle: 'Jahan aapki awaaz wala server chal raha hai (Hugging Face / PC)',
        child: Column(children: [
          TextField(controller: _server, decoration: const InputDecoration(hintText: 'https://xxxx.hf.space')),
          const SizedBox(height: 12),
          GradientButton(label: 'Server save karo', height: 48, loading: _saving, onTap: () => _save('Server URL', {'serverUrl': _server.text.trim()})),
        ]),
      ),
    ]);
  }
}

class _Card extends StatelessWidget {
  const _Card({required this.icon, required this.title, required this.subtitle, required this.child});
  final IconData icon;
  final String title, subtitle;
  final Widget child;

  @override
  Widget build(BuildContext context) => Padding(
        padding: const EdgeInsets.only(bottom: 14),
        child: Glass(
          child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
            Row(children: [
              IconBubble(icon: icon, size: 40),
              const SizedBox(width: 12),
              Expanded(
                child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  Text(title, style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
                  Text(subtitle, style: TextStyle(fontSize: 12, color: Theme.of(context).hintColor)),
                ]),
              ),
            ]),
            const SizedBox(height: 14),
            child,
          ]),
        ),
      );
}
