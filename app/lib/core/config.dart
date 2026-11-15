/// Sagar Vaani - App configuration.
///
/// Firebase values GitHub Actions build ke time `--dart-define` se aate hain
/// (GitHub secret `GOOGLE_SERVICES_JSON` se). Agar set nahi hain to app bina
/// login / admin ke bhi chal jayega.
class AppConfig {
  static const appName = 'Sagar Vaani';
  static const tagline = 'Har page, Sagar ki awaaz mein';

  // Firebase project "sagar-vaani" (google-services.json se). Ye values public hoti hain,
  // suraksha Firestore rules se hoti hai. GitHub secret GOOGLE_SERVICES_JSON ho to wo use hota hai.
  static const fbApiKey = String.fromEnvironment('FB_API_KEY', defaultValue: 'AIzaSyBiAv_uuQxi8gJFo2tsmiXNbiKGV-5KGOo');
  static const fbAppId = String.fromEnvironment('FB_APP_ID', defaultValue: '1:294146008592:android:a9c182d23e830c731d0c95');
  static const fbSenderId = String.fromEnvironment('FB_SENDER_ID', defaultValue: '294146008592');
  static const fbProjectId = String.fromEnvironment('FB_PROJECT_ID', defaultValue: 'sagar-vaani');
  static const fbStorageBucket = String.fromEnvironment('FB_STORAGE_BUCKET', defaultValue: 'sagar-vaani.firebasestorage.app');

  static bool get firebaseConfigured =>
      fbApiKey.isNotEmpty && fbAppId.isNotEmpty && fbProjectId.isNotEmpty;

  /// Voice/AI server ka default URL. Admin panel se kabhi bhi badal sakte ho.
  static const defaultServerUrl = String.fromEnvironment('SERVER_URL');

  /// Firebase na ho to control isi GitHub JSON se hota hai (aapke sagar-saver jaisa).
  static const githubConfigUrl =
      'https://raw.githubusercontent.com/1sagargamer-web/sagar-baby/main/config/sagar-vaani.json';

  /// Naya APK hamesha isi link pe milega (GitHub Releases, fixed tag - Sagar Saver se alag).
  static const defaultUpdateUrl =
      'https://github.com/1sagargamer-web/sagar-baby/releases/download/sagar-vaani-latest/SagarVaani.apk';
}
