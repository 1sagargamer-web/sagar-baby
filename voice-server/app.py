"""
Sagar Vaani - Voice + AI server.

- /tts   : Text -> MP3, sirf owner (Sagar) ki cloned awaaz mein (Chatterbox Multilingual, MIT, open-source)
- /ocr   : Photo / PDF / handwritten notes -> text (Gemini free tier)
- /ai    : summary / translate / ask (Gemini free tier)
- /admin/push : sab users ko push notification (Firebase Cloud Messaging)

Secrets environment variables se aate hain (kabhi code mein mat likhna):
  GEMINI_API_KEY            - Google AI Studio ki free key
  GEMINI_MODEL              - default "gemini-2.5-flash"
  FIREBASE_SERVICE_ACCOUNT  - Firebase service account JSON (poora JSON text). Optional,
                              par isse login check + block + push kaam karta hai.
  VOICE_SAMPLE              - aapki awaaz ki recording ka path (default voice/sagar.wav)
  VOICE_REPO                - (recommended) private Hugging Face dataset jisme recording hai,
                              jaise "username/sagar-voice". Isse aapki awaaz public nahi hoti.
  VOICE_FILE                - us repo mein file ka naam (default sagar.wav)
  HF_TOKEN                  - Hugging Face token (private repo padhne ke liye)
"""

import base64
import hashlib
import io
import json
import os
import re
import threading
import time
from pathlib import Path
from typing import List, Optional

import httpx
import numpy as np
from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel

APP_NAME = "Sagar Vaani"
VOICE_SAMPLE = os.getenv("VOICE_SAMPLE", "voice/sagar.wav")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
CACHE_DIR = Path(os.getenv("CACHE_DIR", "/tmp/vaani-cache"))
CACHE_DIR.mkdir(parents=True, exist_ok=True)
MAX_TTS_CHARS = int(os.getenv("MAX_TTS_CHARS", "1200"))



def fetch_private_voice():
    """Private HF repo se voice sample download karo (public Space mein awaaz na rakhni pade)."""
    global VOICE_SAMPLE
    repo = os.getenv("VOICE_REPO", "").strip()
    if not repo:
        return
    try:
        from huggingface_hub import hf_hub_download

        VOICE_SAMPLE = hf_hub_download(
            repo_id=repo,
            filename=os.getenv("VOICE_FILE", "sagar.wav"),
            repo_type=os.getenv("VOICE_REPO_TYPE", "dataset"),
            token=os.getenv("HF_TOKEN"),
        )
        print("[voice] private sample ready")
    except Exception as e:
        print("[voice] private sample download failed:", e)


fetch_private_voice()


def normalize_voice():
    """Phone ki recording (m4a/mp3/aac) ko saaf WAV mein badlo."""
    global VOICE_SAMPLE
    src = Path(VOICE_SAMPLE)
    if not src.exists():
        return
    out = CACHE_DIR / "voice_ref.wav"
    try:
        import subprocess

        subprocess.run(
            ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-ac", "1", "-ar", "24000",
             "-af", "silenceremove=start_periods=1:start_threshold=-45dB,loudnorm", "-t", "30", str(out)],
            check=True,
        )
        VOICE_SAMPLE = str(out)
        print("[voice] sample normalised")
    except Exception as e:
        print("[voice] ffmpeg convert failed, original use hoga:", e)


normalize_voice()

app = FastAPI(title=APP_NAME)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# --------------------------------------------------------------------------------------
# Firebase (optional)
# --------------------------------------------------------------------------------------
_fb_ready = False
_firestore = None
try:
    _sa = os.getenv("FIREBASE_SERVICE_ACCOUNT", "").strip()
    if _sa:
        import firebase_admin
        from firebase_admin import auth as fb_auth
        from firebase_admin import credentials, firestore, messaging

        firebase_admin.initialize_app(credentials.Certificate(json.loads(_sa)))
        _firestore = firestore.client()
        _fb_ready = True
        print("[firebase] ready")
except Exception as e:  # pragma: no cover
    print("[firebase] disabled:", e)


class User(BaseModel):
    uid: str = "guest"
    is_admin: bool = False


def current_user(authorization: Optional[str] = Header(default=None)) -> User:
    """Firebase login token check. Firebase set nahi hai to sabko allow."""
    if not _fb_ready:
        return User()
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "Login zaroori hai")
    try:
        decoded = fb_auth.verify_id_token(authorization.split(" ", 1)[1])
    except Exception:
        raise HTTPException(401, "Login expire ho gaya, dobara login karein")
    uid = decoded["uid"]
    snap = _firestore.collection("users").document(uid).get()
    if snap.exists and snap.to_dict().get("blocked"):
        raise HTTPException(403, "Aapka account block hai")
    is_admin = _firestore.collection("admins").document(uid).get().exists
    return User(uid=uid, is_admin=is_admin)


# --------------------------------------------------------------------------------------
# Voice model (lazy load, ek hi baar)
# --------------------------------------------------------------------------------------
_model = None
_model_lock = threading.Lock()
_gen_lock = threading.Lock()


def get_model():
    global _model
    if _model is not None:
        return _model
    with _model_lock:
        if _model is None:
            import torch
            from chatterbox.mtl_tts import ChatterboxMultilingualTTS

            device = "cuda" if torch.cuda.is_available() else "cpu"
            if device == "cpu":
                torch.set_num_threads(max(1, os.cpu_count() or 1))
            print(f"[tts] loading model on {device} ...")
            m = ChatterboxMultilingualTTS.from_pretrained(device=device)
            if not Path(VOICE_SAMPLE).exists():
                raise RuntimeError(f"Voice sample nahi mila: {VOICE_SAMPLE}")
            m.prepare_conditionals(VOICE_SAMPLE, exaggeration=0.5)
            _model = m
            print("[tts] ready")
    return _model


DEVANAGARI = re.compile(r"[ऀ-ॿ]")
LATIN = re.compile(r"[A-Za-z]")


def detect_lang(text: str) -> str:
    dev = len(DEVANAGARI.findall(text))
    lat = len(LATIN.findall(text))
    return "hi" if dev >= lat * 0.5 and dev > 0 else "en"


def split_sentences(text: str, limit: int = 260) -> List[str]:
    """Lambe text ko chhote tukdon mein todo taaki awaaz natural rahe."""
    text = re.sub(r"\s+", " ", text).strip()
    parts = re.split(r"(?<=[\.\!\?।॥;:])\s+", text)
    out, cur = [], ""
    for p in parts:
        while len(p) > limit:  # bahut lamba vakya -> comma / space pe todo
            cut = max(p.rfind(",", 0, limit), p.rfind(" ", 0, limit))
            cut = cut if cut > 40 else limit
            if cur:
                out.append(cur)
                cur = ""
            out.append(p[:cut].strip())
            p = p[cut:].strip()
        if len(cur) + len(p) + 1 <= limit:
            cur = f"{cur} {p}".strip()
        else:
            if cur:
                out.append(cur)
            cur = p
    if cur:
        out.append(cur)
    return [s for s in out if s.strip()]


def to_mp3(wav: np.ndarray, sr: int) -> bytes:
    import lameenc

    pcm = np.clip(wav, -1.0, 1.0)
    pcm = (pcm * 32767).astype(np.int16).tobytes()
    enc = lameenc.Encoder()
    enc.set_bit_rate(128)
    enc.set_in_sample_rate(sr)
    enc.set_channels(1)
    enc.set_quality(2)
    return bytes(enc.encode(pcm) + enc.flush())


class TTSReq(BaseModel):
    text: str
    lang: str = "auto"  # auto | hi | en


@app.post("/tts")
def tts(req: TTSReq, user: User = Depends(current_user)):
    text = (req.text or "").strip()
    if not text:
        raise HTTPException(400, "Text khaali hai")
    text = text[:MAX_TTS_CHARS]
    key = hashlib.sha256(f"{req.lang}|{text}|{Path(VOICE_SAMPLE).stat().st_mtime if Path(VOICE_SAMPLE).exists() else 0}".encode()).hexdigest()
    cached = CACHE_DIR / f"{key}.mp3"
    if cached.exists():
        return Response(cached.read_bytes(), media_type="audio/mpeg")

    model = get_model()
    pieces = []
    silence = np.zeros(int(model.sr * 0.18), dtype=np.float32)
    with _gen_lock:  # ek time pe ek generation (CPU / GPU memory bachane ke liye)
        for sent in split_sentences(text):
            lang = req.lang if req.lang in ("hi", "en") else detect_lang(sent)
            wav = model.generate(sent, language_id=lang, exaggeration=0.5, cfg_weight=0.5, temperature=0.75)
            pieces.append(wav.squeeze(0).numpy().astype(np.float32))
            pieces.append(silence)
    audio = np.concatenate(pieces) if pieces else silence
    mp3 = to_mp3(audio, model.sr)
    cached.write_bytes(mp3)
    return Response(mp3, media_type="audio/mpeg")


# --------------------------------------------------------------------------------------
# Gemini helpers (OCR + AI)
# --------------------------------------------------------------------------------------
_model_name = GEMINI_MODEL


def _pick_available_model() -> Optional[str]:
    """Purana model band ho jaye to apne aap koi naya 'flash' model chun lo."""
    try:
        r = httpx.get(
            "https://generativelanguage.googleapis.com/v1beta/models?pageSize=200",
            headers={"x-goog-api-key": GEMINI_API_KEY},
            timeout=30,
        )
        models = [
            m["name"].split("/", 1)[-1]
            for m in r.json().get("models", [])
            if "generateContent" in m.get("supportedGenerationMethods", [])
        ]
    except Exception:
        return None
    bad = ("lite", "image", "tts", "live", "audio", "embed", "exp", "preview", "thinking")
    good = sorted(m for m in models if "flash" in m and not any(b in m for b in bad))
    if good:
        return good[-1]
    return models[0] if models else None


def gemini(parts: list, temperature: float = 0.2) -> str:
    global _model_name
    if not GEMINI_API_KEY:
        raise HTTPException(500, "Server pe GEMINI_API_KEY set nahi hai")
    body = {"contents": [{"role": "user", "parts": parts}], "generationConfig": {"temperature": temperature}}
    switched = False
    for attempt in range(4):
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{_model_name}:generateContent"
        r = httpx.post(url, json=body, headers={"x-goog-api-key": GEMINI_API_KEY}, timeout=120)
        if r.status_code == 404 and not switched:
            new = _pick_available_model()
            if new and new != _model_name:
                print(f"[ai] model {_model_name} nahi mila, ab {new} use hoga")
                _model_name = new
                switched = True
                continue
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(2 * (attempt + 1))
            continue
        if r.status_code != 200:
            raise HTTPException(502, f"AI error: {r.text[:300]}")
        data = r.json()
        try:
            return "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"]).strip()
        except Exception:
            raise HTTPException(502, "AI ne jawab nahi diya, dobara try karein")
    raise HTTPException(503, "AI abhi busy hai, thodi der baad try karein")


OCR_PROMPT = (
    "You are an expert OCR engine for Hindi (Devanagari) and English, including messy HANDWRITTEN notes. "
    "Transcribe ALL text exactly as written, in reading order, keeping the original language and script. "
    "Do not translate, do not summarise, do not add comments. Keep paragraphs and line breaks. "
    "If a word is unclear, write your best guess. If there are multiple pages, separate them with a blank line. "
    "Return only the transcribed text."
)


@app.post("/ocr")
async def ocr(files: List[UploadFile] = File(...), user: User = Depends(current_user)):
    parts = [{"text": OCR_PROMPT}]
    for f in files[:10]:
        raw = await f.read()
        if len(raw) > 18 * 1024 * 1024:
            raise HTTPException(413, "File bahut badi hai (max 18MB)")
        mime = f.content_type or "image/jpeg"
        if f.filename and f.filename.lower().endswith(".pdf"):
            mime = "application/pdf"
        parts.append({"inline_data": {"mime_type": mime, "data": base64.b64encode(raw).decode()}})
    return {"text": gemini(parts, temperature=0.0)}


class AIReq(BaseModel):
    action: str  # summary | translate | ask
    text: str
    question: Optional[str] = None
    target_lang: Optional[str] = None  # "hi" / "en"
    history: Optional[List[dict]] = None  # [{"q":..., "a":...}]


LANG_NAME = {"hi": "Hindi (Devanagari script)", "en": "English"}


@app.post("/ai")
def ai(req: AIReq, user: User = Depends(current_user)):
    text = (req.text or "")[:60000]
    if req.action == "summary":
        lang = LANG_NAME.get(req.target_lang or detect_lang(text), "Hindi (Devanagari script)")
        prompt = (
            f"Summarise the following page in {lang}. Write 4-7 short, clear sentences that a person can listen to. "
            "No markdown, no bullet symbols, no emojis.\n\nPAGE:\n" + text
        )
        return {"text": gemini([{"text": prompt}], 0.3)}
    if req.action == "translate":
        lang = LANG_NAME.get(req.target_lang or "hi", "Hindi (Devanagari script)")
        prompt = (
            f"Translate the following text into natural, simple {lang}. Keep meaning exact, keep paragraphs. "
            "Return only the translation, no notes.\n\nTEXT:\n" + text
        )
        return {"text": gemini([{"text": prompt}], 0.1)}
    if req.action == "ask":
        if not req.question:
            raise HTTPException(400, "Sawaal khaali hai")
        hist = ""
        for h in (req.history or [])[-6:]:
            hist += f"Q: {h.get('q','')}\nA: {h.get('a','')}\n"
        prompt = (
            "You are Sagar Vaani, a careful, accurate study assistant. Answer the user's question. "
            "Use the PAGE below as the main source. If the page does not contain the answer, answer from reliable "
            "general knowledge and clearly say it is not from the page. Never invent facts; if unsure, say so. "
            "Reply in the same language as the question (Hindi in Devanagari if the question is Hindi/Hinglish). "
            "Keep it short and easy to listen to (max ~120 words). No markdown, no emojis.\n\n"
            f"PAGE:\n{text}\n\nPREVIOUS:\n{hist}\nQUESTION: {req.question}"
        )
        return {"text": gemini([{"text": prompt}], 0.2)}
    raise HTTPException(400, "Galat action")


# --------------------------------------------------------------------------------------
# Admin
# --------------------------------------------------------------------------------------
class PushReq(BaseModel):
    title: str
    body: str


@app.post("/admin/push")
def admin_push(req: PushReq, user: User = Depends(current_user)):
    if not _fb_ready:
        raise HTTPException(500, "Server pe FIREBASE_SERVICE_ACCOUNT set nahi hai")
    if not user.is_admin:
        raise HTTPException(403, "Sirf owner hi notice bhej sakta hai")
    msg = messaging.Message(
        topic="all",
        notification=messaging.Notification(title=req.title, body=req.body),
        android=messaging.AndroidConfig(priority="high"),
    )
    return {"id": messaging.send(msg)}


@app.get("/")
@app.get("/health")
def health():
    return {
        "app": APP_NAME,
        "ok": True,
        "voice_sample": Path(VOICE_SAMPLE).exists(),
        "voice_loaded": _model is not None,
        "ai": bool(GEMINI_API_KEY),
        "ai_model": _model_name,
        "firebase": _fb_ready,
    }


@app.on_event("startup")
def warmup():
    # Model ko background mein load karo taaki pehla user wait na kare
    if os.getenv("PRELOAD", "1") == "1" and Path(VOICE_SAMPLE).exists():
        threading.Thread(target=lambda: _safe(get_model), daemon=True).start()


def _safe(fn):
    try:
        fn()
    except Exception as e:
        print("[warmup] failed:", e)
