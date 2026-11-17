"""Original sound effects for the gaming channel, all synthesised here (no licence issues).

Usage:  python3 scripts/make_gaming_sfx.py [out_dir]      (default: sfx/gaming/)
Writes: whoosh.wav, impact.wav, riser.wav, glitch.wav, pop.wav, ding.wav, bass-drop.wav, error.wav, click.wav,
        swell.wav

Where they go (make_gaming_video.py): title card / word card -> whoosh (+ impact on big words); zoom -> whoosh;
callout box -> pop; kill -> ding; before a reveal -> riser (or swell), reveal -> bass-drop + impact;
ban notice / "scam" -> glitch + error; menu/typing -> click. The first channel's sfx/ files are untouched.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

SR = 48000
rng = np.random.default_rng(7)
HERE = Path(__file__).resolve().parent.parent


def filt(x, kind, freq, order=2):
    return sosfilt(butter(order, freq, btype=kind, fs=SR, output="sos"), x)


def sweep_bp(noise, f0, f1, steps=40):
    """Band-pass noise whose centre moves from f0 to f1 (block-wise)."""
    out = np.zeros_like(noise)
    edges = np.linspace(0, len(noise), steps + 1).astype(int)
    for i in range(steps):
        fc = f0 * (f1 / f0) ** (i / (steps - 1))
        a, b = edges[i], edges[i + 1]
        pad = 2048
        lo, hi = max(0, a - pad), min(len(noise), b + pad)
        seg = filt(noise[lo:hi], "bandpass", [max(40, fc * 0.6), min(SR / 2 - 100, fc * 1.6)])
        out[a:b] = seg[a - lo:a - lo + (b - a)]
    return out


def t_(dur):
    return np.arange(int(dur * SR)) / SR


def stereo(x, pan_from=0.0, pan_to=0.0):
    p = np.linspace(pan_from, pan_to, len(x))
    return np.stack([x * np.sqrt((1 - p) / 2), x * np.sqrt((1 + p) / 2)], 1)


def whoosh():
    t = t_(0.45)
    x = sweep_bp(rng.normal(0, 1, len(t)), 300, 4000)
    env = np.sin(np.pi * (t / t[-1]) ** 0.7) ** 2
    return stereo(x * env, -0.7, 0.7)


def impact():
    t = t_(1.4)
    f = 38 + 90 * np.exp(-t / 0.05)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.45)
    crack = filt(rng.normal(0, 1, len(t)), "bandpass", [800, 6000]) * np.exp(-t / 0.03)
    tail = filt(rng.normal(0, 1, len(t)), "lowpass", 400) * np.exp(-t / 0.5) * 0.25
    return stereo(np.tanh((body * 1.4 + crack * 0.6 + tail) * 1.5))


def riser():
    t = t_(2.5)
    u = t / t[-1]
    noise = sweep_bp(rng.normal(0, 1, len(t)), 200, 9000, 60) * u ** 2
    f = 110 * 2 ** (u * 3)  # three octaves up
    tone = sum(np.sin(2 * np.pi * np.cumsum(f * h) / SR) / h for h in (1, 2, 3)) * 0.25 * u ** 1.5
    x = noise * 0.8 + tone
    x[-int(0.01 * SR):] *= np.linspace(1, 0, int(0.01 * SR))
    return stereo(x)


def glitch():
    t = t_(0.6)
    x = np.zeros(len(t))
    pos = 0
    while pos < len(t):
        n = int(rng.uniform(0.015, 0.06) * SR)
        kind = rng.integers(0, 3)
        tt = np.arange(n) / SR
        if kind == 0:
            seg = np.sign(np.sin(2 * np.pi * rng.uniform(200, 1800) * tt))  # square buzz
        elif kind == 1:
            seg = np.round(rng.normal(0, 1, n) * 3) / 3  # crushed noise
        else:
            seg = np.zeros(n)  # dropout
        x[pos:pos + n] = seg[: len(x) - pos] * rng.uniform(0.3, 0.8)
        pos += n
    return stereo(filt(x, "highpass", 150) * 0.6, rng.uniform(-0.5, 0), rng.uniform(0, 0.5))


def pop():
    t = t_(0.12)
    f = 300 + 900 * np.exp(-t / 0.01)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.03)
    return stereo(x * 0.9)


def ding():
    t = t_(0.9)
    x = sum(a * np.sin(2 * np.pi * 1318.5 * r * t) * np.exp(-t / d)
            for a, r, d in [(1, 1, 0.35), (0.5, 2.0, 0.2), (0.3, 3.01, 0.12), (0.4, 1.5, 0.3)])
    return stereo(x * 0.35)


def bass_drop():
    t = t_(1.6)
    f = 140 * np.exp(-t / 0.35) + 32
    x = np.tanh(np.sin(2 * np.pi * np.cumsum(f) / SR) * 2.2) * np.minimum(1, t / 0.005) * np.exp(-t / 0.7)
    return stereo(x * 0.9)


def error():
    t = t_(0.7)
    gate = ((t % 0.18) < 0.13).astype(float)
    x = (np.sign(np.sin(2 * np.pi * 180 * t)) * 0.5 + np.sign(np.sin(2 * np.pi * 186 * t)) * 0.5) * gate
    return stereo(filt(x, "lowpass", 2500) * 0.4)


def click():
    t = t_(0.05)
    x = filt(rng.normal(0, 1, len(t)), "bandpass", [2000, 8000]) * np.exp(-t / 0.004)
    return stereo(x * 0.8)


def swell():
    x = riser()[:, 0]
    return stereo(x[::-1].copy() * np.linspace(0, 1, len(x)) ** 0.5)  # reverse-cymbal style swell


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "sfx" / "gaming"
    out.mkdir(parents=True, exist_ok=True)
    for name, fn in [("whoosh", whoosh), ("impact", impact), ("riser", riser), ("glitch", glitch), ("pop", pop),
                     ("ding", ding), ("bass-drop", bass_drop), ("error", error), ("click", click), ("swell", swell)]:
        x = fn()
        x = x / (np.max(np.abs(x)) + 1e-9) * 0.89  # peak about -1 dB
        with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
            sf.write(tmp.name, x, SR)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp.name, "-c:a", "pcm_s16le", str(out / f"{name}.wav")],
                           check=True)
        print("saved", out / f"{name}.wav")


if __name__ == "__main__":
    main()
