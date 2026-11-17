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
    # Whisper often skips repeated takes, so also cut on pauses: every sound island, and each island joined with the
    # next one (a take can contain a deliberate "..." pause). All candidates are scored the same way.
    hop = int(SR * 0.02)
    db = np.array([20 * np.log10(np.sqrt(np.mean(x[i:i + hop] ** 2)) + 1e-9) for i in range(0, len(x) - hop, hop)])
    loud = db > -40
    islands, s0, quiet = [], None, 0
    for i, v in enumerate(loud):
        if v:
            if s0 is None:
                s0 = i
            quiet = 0
        elif s0 is not None:
            quiet += 1
            if quiet * 0.02 >= 0.4:
                islands.append([s0 * 0.02, (i - quiet + 1) * 0.02]); s0 = None
    if s0 is not None:
        islands.append([s0 * 0.02, len(loud) * 0.02])
    islands = [[max(0, a - 0.12), min(len(x) / SR, b + 0.15)] for a, b in islands if b - a > 0.25]
    cands = [tuple(b) for b in bounds] + [tuple(i) for i in islands]
    cands += [(islands[i][0], islands[i + 1][1]) for i in range(len(islands) - 1)]
    bounds = sorted(set((round(a, 2), round(b, 2)) for a, b in cands))

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
        # a candidate holding two takes reads as "complete" twice over; penalise extra words
        extra = max(0, len(ws) - len(exp_words) - 1) * 0.08
        # sound that Whisper did not transcribe (it drops repeated takes): more sound time than the words explain
        seg_db = np.array([20 * np.log10(np.sqrt(np.mean(seg[i:i + hop] ** 2)) + 1e-9) for i in range(0, len(seg) - hop, hop)])
        active = float(np.sum(seg_db > -40)) * 0.02
        span = (ws[-1]["end"] - ws[0]["start"]) if ws else 0.0
        if active > span * 1.3 + 0.6:
            extra += 0.3
        score = conf * 0.4 + complete * 0.6 - min(clipped, 50) * 0.002 - extra
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
