"""Word-level transcript of a video or audio file with faster-whisper (large-v3).

Usage:
    python3 scripts/transcribe.py Raw/my-reel.mp4 [out.json] [--language hi|en]

Writes JSON: {"language": ..., "words": [{"text", "start", "end", "prob"}], "segments": [...]}
Leave out --language to let Whisper detect it (Hinglish usually works best detected or as "hi").
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
from faster_whisper import WhisperModel

HERE = Path(__file__).resolve().parent.parent
MODEL_DIR = HERE / "models" / "faster-whisper-large-v3"


def main() -> None:
    args = [a for a in sys.argv[1:]]
    language = None
    if "--language" in args:
        i = args.index("--language")
        language = args[i + 1]
        del args[i : i + 2]
    if not args:
        sys.exit(__doc__)
    src = Path(args[0])
    out = Path(args[1]) if len(args) > 1 else src.with_suffix(".transcript.json")

    model = WhisperModel(
        str(MODEL_DIR) if MODEL_DIR.exists() else "large-v3",
        device="cpu",
        compute_type="int8",
        cpu_threads=os.cpu_count() or 4,
    )
    # Decode with FFmpeg (16 kHz mono float) so any phone video format works.
    pcm = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(src), "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
        check=True,
        capture_output=True,
    ).stdout
    audio = np.frombuffer(pcm, dtype=np.float32)
    segments, info = model.transcribe(
        audio,
        language=language,
        word_timestamps=True,
        vad_filter=True,
        beam_size=5,
    )
    words, segs = [], []
    for seg in segments:
        segs.append({"start": round(seg.start, 3), "end": round(seg.end, 3), "text": seg.text.strip()})
        for w in seg.words or []:
            words.append(
                {"text": w.word.strip(), "start": round(w.start, 3), "end": round(w.end, 3), "prob": round(w.probability, 3)}
            )
    out.write_text(json.dumps({"language": info.language, "words": words, "segments": segs}, ensure_ascii=False, indent=1))
    print(f"language={info.language} words={len(words)} -> {out}")


if __name__ == "__main__":
    main()
