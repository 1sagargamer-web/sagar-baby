"""Original sound effects for the reels, all synthesised here (no licence issues).

Usage:  python3 scripts/make_sfx.py <out_dir>
Writes: whoosh.wav, whoosh-short.wav, shimmer.wav, pop.wav, boom.wav, ding.wav

When each one plays (make_reel.py): Bhagwan appears -> whoosh + shimmer; thumbs-up -> pop;
punchline push-in -> whoosh-short; shock + camera shake -> boom.  A line can also ask for one with
"sfx": [{"name": "ding", "at": 0.2}].
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 48000
rng = np.random.default_rng(42)


def onepole(x, alphas):
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += alphas[i] * (v - acc)
        y[i] = acc
    return y


def whoosh(dur):
    n = int(dur * SR)
    t = np.linspace(0, 1, n)
    noise = rng.normal(0, 1, n)
    sweep = 0.02 + 0.35 * np.sin(np.pi * t) ** 2  # filter opens then closes
    body = onepole(noise, sweep) - onepole(noise, sweep * 0.15)  # band-pass-ish
    amp = np.sin(np.pi * t) ** 1.5
    left = body * amp * (1 - 0.6 * t)
    right = body * amp * (0.4 + 0.6 * t)  # moves left -> right
    return np.stack([left, right], 1)


def shimmer():
    n = int(1.6 * SR)
    out = np.zeros(n)
    notes = [1046.5, 1174.7, 1318.5, 1568.0, 1760.0, 2093.0]  # C6 pentatonic, rising sparkle
    for i, f in enumerate(notes):
        s = int(i * 0.07 * SR)
        m = n - s
        t = np.arange(m) / SR
        bell = (np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2.76 * t)
                + 0.25 * np.sin(2 * np.pi * f * 5.4 * t)) * np.exp(-t * 3.5)
        out[s:] += bell * (0.9 - i * 0.08)
    return np.stack([out, np.roll(out, 400)], 1)


def pop():
    n = int(0.18 * SR)
    t = np.arange(n) / SR
    f = 300 + 700 * np.exp(-t * 60)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 30)
    x[:200] += rng.normal(0, 0.3, 200) * np.linspace(1, 0, 200)
    return np.stack([x, x], 1)


def boom():
    n = int(1.6 * SR)
    t = np.arange(n) / SR
    f = 38 + 50 * np.exp(-t * 7)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)
    hit = onepole(rng.normal(0, 1, n), np.full(n, 0.08)) * np.exp(-t * 18) * 2.5
    x = np.tanh((sub + hit) * 2.2)  # a little grit so it reads on phone speakers
    mid = np.sin(2 * np.pi * 110 * t) * np.exp(-t * 9) * 0.35  # harmonic phones can play
    x = x + mid
    return np.stack([x, x], 1)


def ding():
    n = int(1.0 * SR)
    t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * 1318.5 * t) + 0.4 * np.sin(2 * np.pi * 1318.5 * 2.0 * t)) * np.exp(-t * 4)
    return np.stack([x, x], 1)


def save(x, path, lufs=-18, reverb=False):
    x = x / max(1e-9, np.max(np.abs(x))) * 0.8
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        sf.write(tmp.name, x, SR)
        af = ("aecho=0.8:0.6:70|140:0.3|0.2," if reverb else "") + f"loudnorm=I={lufs}:TP=-1.5"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp.name, "-af", af, "-ar", "48000", str(path)], check=True)


def main() -> None:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    save(whoosh(0.7), out / "whoosh.wav")
    save(whoosh(0.32), out / "whoosh-short.wav")
    save(shimmer(), out / "shimmer.wav", reverb=True)
    save(pop(), out / "pop.wav")
    save(boom(), out / "boom.wav", lufs=-14)
    save(ding(), out / "ding.wav", reverb=True)
    print("saved sfx to", out)


if __name__ == "__main__":
    main()
