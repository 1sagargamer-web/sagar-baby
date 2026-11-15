# 🌊 Sagar Vaani — Har page, Sagar ki awaaz mein

Android app jo koi bhi page (camera scan, photo, PDF, text, website) padh ke **Sagar ki asli awaaz** mein sunata hai.

## Features
- 📷 **Live camera scan**, ek saath kai page bhi
- 🖼️ Photo, 📄 PDF (scanned bhi), 📝 Text, 🌐 Website link, ek se zyada file ek saath
- ✍️ Hindi + English, **handwritten notes** bhi
- 🔊 Poora page ya **sirf select kiya hua** text suno
- ⏩ Speed 0.5x se 2x, pause/resume, aage/peeche
- 🔒 **Background + lock screen** pe bhi chalta rahe (notification se control)
- ⬇️ **MP3 download** + **WhatsApp share**
- 🌍 **Translate karke suno** (English → Hindi, Hindi → English)
- 📌 Page ka **chhota saar (summary)** awaaz mein
- 🤖 **AI se sawaal poocho**, jawab Sagar ki awaaz mein
- 📚 Library, history, bookmark
- 🌙 Dark / Light mode, bada font
- 👑 **Owner Panel:** kaun-kaun use kar raha hai, kya kar raha hai (kya poochha, kya padha), user block/unblock, maintenance mode, notice + push notification, update link (normal ya force update), server URL

## Folder
| Folder | Kya hai |
|---|---|
| `app/` | Flutter Android app |
| `voice-server/` | Voice (Chatterbox, open-source) + AI server, Hugging Face Space pe free chalega |
| `firebase/firestore.rules` | Database security rules |
| `config/sagar-vaani.json` | Firebase na ho to isi file se maintenance/notice/update control |
| `.github/workflows/build-apk.yml` | Har push pe APK banata hai → GitHub Releases |

---

## Setup — step by step (sab free)

### Step 1 — Signing key (sirf ek baar)
GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**.
Mujhe (Claude ko) jo `SagarVaani-signing-secrets.txt` mila hai, usme ke 4 secrets daalo:
`KEY_ALIAS`, `KEYSTORE_PASSWORD`, `KEY_PASSWORD`, `KEYSTORE_BASE64`.
> Ye file Google Drive mein sambhal ke rakhna. Iske bina naya update purane app ke upar install nahi hoga.

### Step 2 — Firebase (login + Owner Panel + notification)
1. https://console.firebase.google.com → **Add project** → naam `sagar-vaani` (Analytics band kar sakte ho).
2. **Android app add karo**, package name: `com.sagar.sagar_vaani` → `google-services.json` download karo.
3. Us file ka **poora text copy** karke GitHub secret banao: `GOOGLE_SERVICES_JSON`.
4. **Build → Authentication → Get started → Email/Password → Enable**.
5. **Build → Firestore Database → Create database** (location: `asia-south1 (Mumbai)`) → **Rules** tab → `firebase/firestore.rules` ka text paste → **Publish**.
6. Naya APK install karo (Step 5), app mein apna account banao.
7. Firebase → **Authentication → Users** → apna **User UID** copy karo.
   Firestore → **Start collection** → ID: `admins` → Document ID: *(apna UID)* → field `role` = `owner` → Save.
8. App band karke kholo → neeche **👑 Owner** tab aa jayega.

### Step 3 — Gemini key (OCR + AI, free)
https://aistudio.google.com → **Get API key → Create API key** → copy karke rakho (Step 4 mein lagegi).

### Step 4 — Voice server (Hugging Face, free)
1. https://huggingface.co pe account banao.
2. **Apni awaaz record karo:** 20–30 second, shaant kamre mein, normal speed mein kuch padho (Hindi + thodi English). File ka naam `sagar.wav` (ya `sagar.mp3`).
3. **New Dataset** → naam `sagar-voice` → **Private** ✅ → `sagar.wav` upload karo.
4. **Settings → Access Tokens → New token (Read)** → copy.
5. **New Space** → naam `sagar-vaani-voice` → SDK: **Docker** → Blank → **Public**.
   `voice-server/` folder ki files (`app.py`, `requirements.txt`, `Dockerfile`, `README.md`) Space mein upload karo.
6. Space → **Settings → Variables and secrets** → ye secrets daalo:
   `GEMINI_API_KEY`, `HF_TOKEN`, `VOICE_REPO` = `aapka-username/sagar-voice`, (mp3 ho to `VOICE_FILE` = `sagar.mp3`),
   aur Firebase → Project settings → Service accounts → **Generate new private key** ka poora JSON → `FIREBASE_SERVICE_ACCOUNT`.
7. Build hone do (10–20 min). Space URL hoga: `https://aapka-username-sagar-vaani-voice.hf.space`
8. App → **Owner → Control → Voice Server URL** mein ye URL daal ke Save. *(Ya GitHub secret `SERVER_URL` bana do, naye APK mein default ho jayega.)*
9. Owner → Dashboard → **Server check karo**: sab ✅ hona chahiye.

> ⚠️ **Speed ki sachchai:** free Hugging Face CPU pe awaaz banne mein har line ke kuch second (kabhi 10–30 sec) lagte hain. Pehla hissa bante hi app bolna shuru kar deta hai, aur baaki peeche se banta rehta hai. Bahut tez chahiye to apne PC (NVIDIA GPU) pe server chala ke Cloudflare tunnel ka URL daal do (`voice-server/README.md` dekho), ye bhi free hai.

### Step 5 — APK lo
- Har push pe GitHub **Actions** APK banata hai → **Releases** mein `SagarVaani.apk`.
- `SagarVaani.apk` = lagbhag sab phone (arm64), `SagarVaani-arm32.apk` = purane phone.
- `main` branch pe push hote hi `sagar-vaani-latest` release update hota hai. Users ka update link hamesha ye hai:
  `https://github.com/1sagargamer-web/sagar-baby/releases/download/sagar-vaani-latest/SagarVaani.apk`
  (Sagar Saver ke releases se alag hai, dono apps ka link kabhi nahi takrayega.)

### Naya update kaise bhejein
1. Code `main` pe push → naya release banega (build number = release ke naam mein).
2. App → **Owner → Control → App Update** → *Latest build no.* mein wo number → Save.
   Sab users ko "Naya update aaya" dikhega. Zaroori update ho to *Force (min) build* mein bhi wahi number daalo, tab bina update kiye app nahi chalega.

### Maintenance / Notice
Owner → Control → Maintenance ON → Save: sabka app band (sirf aapka chalega).
Notice likho → **Sabko bhejo**: sabke phone pe popup + push notification.
*(Firebase setup na kiya ho to yahi sab `config/sagar-vaani.json` edit karke bhi ho jata hai, bilkul aapke sagar-saver jaisa.)*
