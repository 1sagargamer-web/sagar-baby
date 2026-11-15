import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_animate/flutter_animate.dart';
import 'package:material_ui/material_ui.dart';
import 'package:provider/provider.dart';

import '../core/config.dart';
import '../services/backend.dart';
import '../widgets/common.dart';

class AuthScreen extends StatefulWidget {
  const AuthScreen({super.key});

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  bool _signup = true;
  bool _loading = false;
  bool _hide = true;
  final _name = TextEditingController();
  final _email = TextEditingController();
  final _pass = TextEditingController();

  String _msg(Object e) {
    if (e is FirebaseAuthException) {
      switch (e.code) {
        case 'email-already-in-use':
          return 'Ye email pehle se registered hai, Login karein';
        case 'invalid-email':
          return 'Email sahi nahi hai';
        case 'weak-password':
          return 'Password kam se kam 6 akshar ka rakhein';
        case 'user-not-found':
        case 'wrong-password':
        case 'invalid-credential':
          return 'Email ya password galat hai';
        case 'network-request-failed':
          return 'Internet check karein';
        case 'too-many-requests':
          return 'Bahut baar try kiya, thodi der baad karein';
      }
      return e.message ?? 'Kuch gadbad hui';
    }
    return 'Kuch gadbad hui, dobara try karein';
  }

  Future<void> _submit() async {
    final b = context.read<Backend>();
    if (_signup && _name.text.trim().isEmpty) return toast(context, 'Apna naam likhiye');
    if (_email.text.trim().isEmpty || _pass.text.isEmpty) return toast(context, 'Email aur password daaliye');
    setState(() => _loading = true);
    try {
      _signup ? await b.signUp(_name.text, _email.text, _pass.text) : await b.signIn(_email.text, _pass.text);
    } catch (e) {
      if (mounted) toast(context, _msg(e));
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _forgot() async {
    if (_email.text.trim().isEmpty) return toast(context, 'Pehle upar email likhiye');
    try {
      await context.read<Backend>().resetPassword(_email.text);
      if (mounted) toast(context, 'Password reset link email pe bhej diya ✉️');
    } catch (e) {
      if (mounted) toast(context, _msg(e));
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: OceanBackground(
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: Column(children: [
                VaaniLogo(size: 92).animate().scale(duration: 700.ms, curve: Curves.easeOutBack),
                const SizedBox(height: 22),
                GradientText(AppConfig.appName, style: const TextStyle(fontSize: 32, fontWeight: FontWeight.w800)),
                const SizedBox(height: 6),
                Text(AppConfig.tagline, style: TextStyle(color: Theme.of(context).hintColor)),
                const SizedBox(height: 30),
                Glass(
                  padding: const EdgeInsets.all(22),
                  child: Column(crossAxisAlignment: CrossAxisAlignment.stretch, children: [
                    _Toggle(signup: _signup, onChange: (v) => setState(() => _signup = v)),
                    const SizedBox(height: 22),
                    AnimatedSize(
                      duration: const Duration(milliseconds: 300),
                      curve: Curves.easeOutCubic,
                      child: _signup
                          ? Padding(
                              padding: const EdgeInsets.only(bottom: 14),
                              child: TextField(
                                controller: _name,
                                textCapitalization: TextCapitalization.words,
                                decoration: const InputDecoration(hintText: 'Aapka naam', prefixIcon: Icon(Icons.person_rounded)),
                              ),
                            )
                          : const SizedBox(width: double.infinity),
                    ),
                    TextField(
                      controller: _email,
                      keyboardType: TextInputType.emailAddress,
                      decoration: const InputDecoration(hintText: 'Email', prefixIcon: Icon(Icons.alternate_email_rounded)),
                    ),
                    const SizedBox(height: 14),
                    TextField(
                      controller: _pass,
                      obscureText: _hide,
                      onSubmitted: (_) => _submit(),
                      decoration: InputDecoration(
                        hintText: 'Password',
                        prefixIcon: const Icon(Icons.lock_rounded),
                        suffixIcon: IconButton(
                          icon: Icon(_hide ? Icons.visibility_rounded : Icons.visibility_off_rounded),
                          onPressed: () => setState(() => _hide = !_hide),
                        ),
                      ),
                    ),
                    if (!_signup)
                      Align(
                        alignment: Alignment.centerRight,
                        child: TextButton(onPressed: _forgot, child: const Text('Password bhool gaye?')),
                      ),
                    const SizedBox(height: 18),
                    GradientButton(
                      label: _signup ? 'Account banao' : 'Login karo',
                      icon: Icons.arrow_forward_rounded,
                      loading: _loading,
                      onTap: _submit,
                    ),
                  ]),
                ).animate(delay: 200.ms).fadeIn(duration: 500.ms).slideY(begin: 0.15, curve: Curves.easeOutCubic),
              ]),
            ),
          ),
        ),
      ),
    );
  }
}

class _Toggle extends StatelessWidget {
  const _Toggle({required this.signup, required this.onChange});
  final bool signup;
  final ValueChanged<bool> onChange;

  @override
  Widget build(BuildContext context) {
    final dark = isDark(context);
    return Container(
      height: 50,
      padding: const EdgeInsets.all(4),
      decoration: BoxDecoration(
        color: dark ? Colors.white.withValues(alpha: 0.06) : Colors.black.withValues(alpha: 0.05),
        borderRadius: BorderRadius.circular(25),
      ),
      child: Stack(children: [
        AnimatedAlign(
          duration: const Duration(milliseconds: 300),
          curve: Curves.easeOutCubic,
          alignment: signup ? Alignment.centerLeft : Alignment.centerRight,
          child: FractionallySizedBox(
            widthFactor: 0.5,
            child: Container(decoration: BoxDecoration(gradient: const LinearGradient(colors: [Color(0xFF00E0C6), Color(0xFF2F7BFF)]), borderRadius: BorderRadius.circular(21))),
          ),
        ),
        Row(children: [
          for (final s in [true, false])
            Expanded(
              child: GestureDetector(
                behavior: HitTestBehavior.opaque,
                onTap: () => onChange(s),
                child: Center(
                  child: Text(
                    s ? 'Naya Account' : 'Login',
                    style: TextStyle(fontWeight: FontWeight.w600, color: signup == s ? Colors.white : Theme.of(context).hintColor),
                  ),
                ),
              ),
            ),
        ]),
      ]),
    );
  }
}
