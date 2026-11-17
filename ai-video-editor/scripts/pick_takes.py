"""Pick the best take of a line from Sagar's recording (he often says each line 2 times).

Usage:
    python3 scripts/pick_takes.py <recording> "<expected Hindi text>" <out.wav>

Finds where each take starts (the line's first word said again), scores every take on
Whisper confidence, how complete it is, and clipping, then saves the best one de-clipped.
Prints the scores so the choice can be reported.
"""
import difflib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent.parent
SR = 48000


def load(path):
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(pcm, dtype=np.float32)


def transcribe(path):
    with tempfile.NamedTemporaryFile(suffix=".json") as tmp:
        subprocess.run([sys.executable, str(HERE / "scripts" / "transcribe.py"), str(path), tmp.name, "--language", "hi"],
                       check=True, capture_output=True)
        return json.load(open(tmp.name))["words"]


def norm(w):
    return "".join(ch for ch in w if ch.isalnum())


def sim(a, b):
    return difflib.SequenceMatcher(None, norm(a), norm(b)).ratio()


def quiet_point(x, a, b):
    hop = int(SR * 0.01)
    seg = x[int(a * SR):int(b * SR)]
    if len(seg) <= hop:
        return (a + b) / 2
    e = [np.mean(seg[i:i + hop] ** 2) for i in range(0, len(seg) - hop, hop)]
    return a + int(np.argmin(e)) * 0.01


def main() -> None:
    rec, expected, out = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
    x = load(rec)
    words = transcribe(rec)
    exp_words = [w for w in expected.replace("...", " ").split() if norm(w)]
    first = exp_words[0]
    # a new take starts where the first word comes again after at least half a line of words
    starts = [0]
    for i, w in enumerate(words):
        if i - starts[-1] >= max(1, len(exp_words) // 2) and sim(w["text"], first) > 0.6:
            starts.append(i)
    bounds = []
    for k, s in enumerate(starts):
        a = 0.0 if k == 0 else quiet_point(x, words[s - 1]["end"] - 0.05, words[s]["start"] + 0.1)
        b = len(x) / SR if k == len(starts) - 1 else None
        bounds.append([a, b])
    for k in range(len(bounds) - 1):
        bounds[k][1] = bounds[k + 1][0]
    # Whisper sometimes drops a repeated take entirely: if there is lots of audio after the last word, add it
    if words and len(x) / SR - words[-1]["end"] > 1.0 and len(starts) == 1:
        tail_start = words[-1]["end"] + 0.15
        bounds = [[0.0, tail_start], [tail_start, len(x) / SR]]

    results = []
    for k, (a, b) in enumerate(bounds):
        seg = x[int(a * SR):int(b * SR)]
        with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
            sf.write(tmp.name, seg, SR)
            ws = transcribe(tmp.name)
        text = " ".join(w["text"] for w in ws)
        conf = float(np.mean([w["prob"] for w in ws])) if ws else 0.0
        complete = difflib.SequenceMatcher(None, norm(text), norm(expected)).ratio()
        clipped = int(np.sum(np.abs(seg) > 0.985))
        score = conf * 0.5 + complete * 0.5 - min(clipped, 50) * 0.002
        results.append({"take": k + 1, "from": round(a, 2), "to": round(b, 2), "text": text, "confidence": round(conf, 3),
                        "complete": round(complete, 3), "clipped": clipped, "score": round(score, 3)})
    best = max(results, key=lambda r: r["score"])
    for r in results:
        print(json.dumps(r, ensure_ascii=False) + ("  <- best" if r is best else ""))
    a, b = best["from"], best["to"]
    seg = x[int(a * SR):int(b * SR)]
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        sf.write(tmp.name, seg, SR)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp.name, "-af", "adeclip,highpass=f=70", "-ar", str(SR),
                        str(out)], check=True)
    print("saved", out)


if __name__ == "__main__":
    main()
