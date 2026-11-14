# 🎬 Video Downloader

Video ka link paste karo → quality chuno → download. YouTube, Instagram, Facebook, X/Twitter, Vimeo aur 1000+ sites support karta hai ([yt-dlp](https://github.com/yt-dlp/yt-dlp) ki madad se).

## 📱 Sagar Saver — Android APK

**Download:** https://github.com/1sagargamer-web/sagar-baby/releases/latest/download/SagarSaver-arm64.apk

- Purane phone pe install na ho to `SagarSaver-arm32.apk` lo: https://github.com/1sagargamer-web/sagar-baby/releases/latest
- YouTube/Instagram/Facebook app me **Share → Sagar Saver** se bhi link bhej sakte ho.
- Files `Downloads/SagarSaver` folder me save hoti hain.

### 👑 Owner Panel (sirf Sagar ke liye)
App me upar **logo pe 7 baar jaldi-jaldi tap** karo → Owner Panel khulega.

Pehli baar GitHub token chahiye (sirf aapke phone me save hota hai):
1. github.com → Settings → Developer settings → Personal access tokens → **Fine-grained tokens** → Generate new token
2. Repository access: **Only select repositories → sagar-baby**
3. Permissions → Repository permissions → **Contents: Read and write**
4. Token copy karke Owner Panel me paste karo

Owner Panel se:
- 📢 **Sabko message** — app kholne pe popup + notification
- 🛠 **Maintenance mode** — sabke liye app band (owner ke phone pe chalta rahega)
- 🚀 **Force update** — purane version wale bina update kiye app nahi chala payenge

Settings `main` branch ki `config/sagar-saver.json` file me save hoti hain. Users tak pahunchne me ~5 minute lag sakte hain.

**Naya update kaise dein:** `android/` folder me code badlo aur push karo → GitHub Actions naya APK bana ke release kar dega → sabko app me "Update" button dikhega.

## Features (website version)
- Link daalte hi video ka title, thumbnail aur duration dikhta hai
- Quality choose karo: Best, 1080p, 720p, 480p, 360p
- 🎵 Sirf audio (MP3) bhi nikal sakte ho
- Live progress bar, speed aur ETA
- Mobile pe bhi achha dikhta hai

## Kaise chalayein (Windows / Mac / Linux)

1. **Python 3.9+** install karo: https://www.python.org/downloads/ (Windows pe "Add Python to PATH" tick karna)
2. **ffmpeg** install karo (HD video aur MP3 ke liye zaroori):
   - Windows: `winget install ffmpeg`
   - Mac: `brew install ffmpeg`
   - Linux: `sudo apt install ffmpeg`
3. Is folder me terminal kholo aur chalao:
   ```bash
   pip install -r requirements.txt
   python app.py
   ```
4. Browser me kholo: **http://127.0.0.1:5000**

## Android (Termux) pe
```bash
pkg install python ffmpeg git
git clone <is-repo-ka-link> && cd sagar-baby
pip install -r requirements.txt
python app.py
```
Phir phone ke browser me `http://127.0.0.1:5000` kholo.

## Agar koi video download na ho
Sites apna system badalti rehti hain, isliye yt-dlp ko update karo:
```bash
pip install -U yt-dlp
```

## Note
Sirf wahi videos download karo jinka aapko haq hai ya jo personal use ke liye allowed hain. Har site ke apne rules (Terms of Service) hote hain.
