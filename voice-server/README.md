---
title: Sagar Vaani Voice
emoji: 🌊
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
---

# Sagar Vaani – Voice + AI Server

Ye server Sagar Vaani app ke liye 3 kaam karta hai:

| Endpoint | Kaam | Kisse |
|---|---|---|
| `POST /tts` | Text → MP3, **sirf Sagar ki awaaz mein** | [Chatterbox Multilingual](https://github.com/resemble-ai/chatterbox) (open-source, MIT, Hindi + English) |
| `POST /ocr` | Photo / PDF / handwritten notes → text | Google Gemini (free tier) |
| `POST /ai` | Summary / Translate / Sawaal-jawab | Google Gemini (free tier) |
| `POST /admin/push` | Sab users ko notification | Firebase Cloud Messaging |
| `GET /health` | Server theek hai ya nahi | – |

## Secrets (Hugging Face Space → Settings → Variables and secrets)

| Naam | Kya daalna hai | Zaroori? |
|---|---|---|
| `GEMINI_API_KEY` | aistudio.google.com se free key | Haan (OCR + AI ke liye) |
| `HF_TOKEN` | huggingface.co → Settings → Access Tokens (Read) | Haan (private voice ke liye) |
| `VOICE_REPO` | aapka private dataset, jaise `username/sagar-voice` | Haan |
| `VOICE_FILE` | recording ka naam (default `sagar.wav`) | Nahi |
| `FIREBASE_SERVICE_ACCOUNT` | Firebase service account JSON (poora text) | Recommended (login check, block, push) |
| `GEMINI_MODEL` | default `gemini-2.5-flash` | Nahi |

> Apni awaaz ki recording kabhi bhi public Space mein mat daalna – private dataset (`VOICE_REPO`) mein hi rakhna.

## Apne PC pe chalana (NVIDIA GPU ho to bahut tez)

```bash
cd voice-server
pip install -r requirements.txt   # GPU ke liye: torch CUDA version alag se install karein
export GEMINI_API_KEY=...  VOICE_SAMPLE=voice/sagar.wav
uvicorn app:app --host 0.0.0.0 --port 7860
```

Phone se access ke liye free tunnel: `cloudflared tunnel --url http://localhost:7860` → jo `https://….trycloudflare.com` URL mile, use Owner Panel → Server URL mein daal do.
