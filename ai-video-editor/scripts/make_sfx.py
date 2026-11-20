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


def boing():
    n = int(0.9 * SR); t = np.arange(n) / SR
    f = 260 + 180 * np.sin(2 * np.pi * 7 * t) * np.exp(-t * 3) - 120 * t
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 3.2)
    return np.stack([x, x], 1)


def scratch():
    n = int(0.55 * SR); t = np.arange(n) / SR
    f = 600 + 1800 * np.abs(np.sin(2 * np.pi * 2.2 * t))
    x = (np.sign(np.sin(2 * np.pi * np.cumsum(f) / SR)) * 0.5 + rng.normal(0, 0.4, n)) * np.exp(-t * 3.5)
    x = onepole(x, np.full(n, 0.35))
    return np.stack([x, x], 1)


def sadtrombone():
    notes = [(233, 0.45), (220, 0.45), (208, 0.45), (196, 1.2)]
    out = []
    for f, d in notes:
        n = int(d * SR); t = np.arange(n) / SR
        fm = f * (1 + 0.012 * np.sin(2 * np.pi * 6 * t) * np.clip(t * 4, 0, 1))
        if f == 196:
            fm = fm * (1 - 0.06 * t / d)
        ph = 2 * np.pi * np.cumsum(fm) / SR
        w = sum(np.sin(h * ph) / h for h in range(1, 9))
        w = onepole(w, np.full(n, 0.12 + 0.1 * np.sin(np.pi * np.minimum(t / d, 1))))
        out.append(w * np.minimum(1, t * 30) * np.exp(-t * 0.8) * 0.8)
        out.append(np.zeros(int(0.04 * SR)))
    x = np.concatenate(out)
    return np.stack([x, x], 1)


def airhorn():
    n = int(1.3 * SR); t = np.arange(n) / SR
    gate = ((t % 0.42) < 0.30).astype(float) * (t < 1.26)
    f = 520 + 8 * np.sin(2 * np.pi * 18 * t)
    ph = 2 * np.pi * np.cumsum(f) / SR
    w = sum(np.sin(h * ph) / (h ** 0.7) for h in range(1, 12))
    x = np.tanh(w * 0.9) * onepole(gate, np.full(n, 0.01))
    return np.stack([x, x], 1)


def slip():
    n = int(1.0 * SR); t = np.arange(n) / SR
    f = 1800 * np.exp(-t * 3.2) + 200
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2) * (t < 0.62)
    th = int(0.66 * SR); m = n - th; tt = np.arange(m) / SR
    x[th:] += (np.sin(2 * np.pi * 70 * tt) * np.exp(-tt * 14) + onepole(rng.normal(0, 1, m), np.full(m, 0.06)) * np.exp(-tt * 25)) * 1.4
    return np.stack([x, x], 1)


def dundun():
    n = int(1.9 * SR); x = np.zeros(n)
    for start, f in [(0.0, 82.4), (0.62, 61.7)]:
        s0 = int(start * SR); m = n - s0; t = np.arange(m) / SR
        h = np.sin(2 * np.pi * f * t) + 0.5 * np.sin(2 * np.pi * f * 2 * t) + 0.25 * np.sin(2 * np.pi * f * 3 * t)
        x[s0:] += np.tanh(h * 1.6) * np.exp(-t * 3.2)
    return np.stack([x, x], 1)


def bassdrop():
    """Deep 808-style drop with a short riser before it (original 'sigma moment' sound)."""
    n = int(2.2 * SR); t = np.arange(n) / SR
    rise_len = int(0.5 * SR)
    f = 200 + 1200 * (t[:rise_len] / 0.5) ** 2
    riser = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.linspace(0, 0.6, rise_len)
    x = np.zeros(n); x[:rise_len] += riser
    s0 = rise_len + int(0.08 * SR); m = n - s0; tt = np.arange(m) / SR
    fd = 46 + 90 * np.exp(-tt * 14)
    d = np.tanh(np.sin(2 * np.pi * np.cumsum(fd) / SR) * 2.6) * np.exp(-tt * 1.7)
    x[s0:] += d + onepole(rng.normal(0, 1, m), np.full(m, 0.1)) * np.exp(-tt * 30) * 0.8
    return np.stack([x, x], 1)


def bonk():
    n = int(0.5 * SR); t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * 330 * t) + 0.5 * np.sin(2 * np.pi * 740 * t)) * np.exp(-t * 22)
    x += onepole(rng.normal(0, 1, n), np.full(n, 0.3)) * np.exp(-t * 90) * 0.6
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
    for name, fn in [("boing", boing), ("scratch", scratch), ("sadtrombone", sadtrombone), ("airhorn", airhorn),
                     ("slip", slip), ("dundun", dundun), ("bassdrop", bassdrop), ("bonk", bonk)]:
        save(fn(), out / f"{name}.wav", lufs=-16)
    print("saved sfx to", out)


if __name__ == "__main__":
    main()
