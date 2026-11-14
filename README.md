# 🎬 Video Downloader

Video ka link paste karo → quality chuno → download. YouTube, Instagram, Facebook, X/Twitter, Vimeo aur 1000+ sites support karta hai ([yt-dlp](https://github.com/yt-dlp/yt-dlp) ki madad se).

## Features
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
