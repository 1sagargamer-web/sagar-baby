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
| `voice-server/` | Voice (Chatterbox, open-source) + AI server |
| `pc/` | Windows PC pe server ka ek-line setup (`install.ps1`) aur launcher (`run.ps1`) |
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

### Step 4 — Voice server apne Windows PC pe (free)
> Hugging Face ab Docker Spaces ke paise leta hai, isliye server aapke PC pe chalta hai.
> Awaaz ki recording private Hugging Face dataset `sagar5582/sagar-voice` (file `sagar.mp3`) mein hai.

1. PC pe **Start → "PowerShell"** likho → kholo.
2. Ye ek line paste karo (right-click = paste) aur Enter:
   ```
   irm https://raw.githubusercontent.com/1sagargamer-web/sagar-baby/main/pc/install.ps1 | iex
   ```
3. Jo poochhe wo do: Gemini key, Hugging Face token, Firebase key file
   (Firebase → Project settings → Service accounts → *Generate new private key*).
4. Setup khud: Python, AI model (NVIDIA GPU ho to GPU wala), free Cloudflare link, Desktop + Startup shortcut.
5. Server chalu hote hi uska link **apne aap app mein** pahunch jata hai (Firebase `config/app.serverUrl`).
   PC on hone pe server khud start hota hai. Desktop pe **"Sagar Vaani Server"** se bhi chala sakte ho.

PC band = app ki awaaz band (app mein seedha message dikhta hai). Photo OCR tab bhi phone pe chalta hai.

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
