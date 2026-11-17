"""Bhagwan ki fixed awaaz (always the same voice for every video).

Usage:
    python3 scripts/god_voice.py "हे वत्स, कर्म करो, फल की चिंता मत करो।" out.wav

Voice settings live in VOICE below. Do not change them between videos, so the
character always sounds the same. Kokoro (open source, runs locally) makes the
base voice; FFmpeg then lowers the pitch a little and adds a soft temple echo.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import soundfile as sf
from kokoro_onnx import Kokoro

HERE = Path(__file__).resolve().parent.parent
MODEL = HERE / "models" / "kokoro" / "kokoro-v1.0.onnx"
VOICES = HERE / "models" / "kokoro" / "voices-v1.0.bin"

# The one and only Bhagwan voice. Keep these fixed.
VOICE = {
    "voice": "hm_omega",  # Kokoro Hindi male voice
    "speed": 0.92,  # a little slower = calm, wise
    "pitch": 0.90,  # 10% deeper
    "echo": "aecho=0.8:0.6:60:0.18",  # soft divine echo
}


def make(text: str, out: Path, voice: dict = VOICE) -> None:
    kokoro = Kokoro(str(MODEL), str(VOICES))
    samples, rate = kokoro.create(text, voice=voice["voice"], speed=voice["speed"], lang="hi")
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        sf.write(tmp.name, samples, rate)
        p = voice["pitch"]
        af = f"asetrate={rate}*{p},aresample=48000,atempo={1 / p:.4f},{voice['echo']},loudnorm=I=-16:TP=-1.5"
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", tmp.name, "-af", af, "-ac", "1", "-ar", "48000", str(out)],
            check=True,
        )


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    make(sys.argv[1], Path(sys.argv[2]))
    print("saved", sys.argv[2])
