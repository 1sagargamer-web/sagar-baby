"""Original sound effects for the gaming channel, all synthesised here (no licence issues).

Usage:  python3 scripts/make_gaming_sfx.py [out_dir] [--seed N]      (default: sfx/gaming/, the base set)
Writes: whoosh.wav, impact.wav, riser.wav, glitch.wav, pop.wav, ding.wav, bass-drop.wav, error.wav, click.wav,
        swell.wav

--seed N makes a *new variant* of every effect (pitch, length, colour, movement change within a range), so each
video gets its own sound pack (Sagar's rule: never the same SFX in every video). The builder writes one pack per
project with a seed taken from the video name. Without --seed the base set in sfx/gaming/ is reproduced.

Where they go (make_gaming_video.py): title card / word card -> whoosh (+ impact on big words); zoom -> whoosh;
callout box -> pop; kill -> ding; before a reveal -> riser (or swell), reveal -> bass-drop + impact;
ban notice / "scam" -> glitch + error; menu/typing -> click. The first channel's sfx/ files are untouched.
"""
import argparse
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

SR = 48000
HERE = Path(__file__).resolve().parent.parent
rng = np.random.default_rng(7)
VARY = False


def v(base, lo, hi):
    """The base value, or a random value in [lo, hi] when making a variant pack."""
    return float(rng.uniform(lo, hi)) if VARY else base


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
    t = t_(v(0.45, 0.3, 0.7))
    x = sweep_bp(rng.normal(0, 1, len(t)), v(300, 150, 600), v(4000, 2500, 8000))
    env = np.sin(np.pi * (t / t[-1]) ** v(0.7, 0.5, 1.2)) ** 2
    side = 1 if not VARY or rng.random() < 0.5 else -1
    return stereo(x * env, -0.7 * side, 0.7 * side)


def impact():
    t = t_(v(1.4, 1.0, 2.0))
    lo = v(38, 30, 55)
    f = lo + v(90, 60, 160) * np.exp(-t / v(0.05, 0.03, 0.09))
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / v(0.45, 0.3, 0.7))
    crack = filt(rng.normal(0, 1, len(t)), "bandpass", [v(800, 500, 1500), v(6000, 4000, 9000)]) \
        * np.exp(-t / v(0.03, 0.015, 0.05))
    tail = filt(rng.normal(0, 1, len(t)), "lowpass", v(400, 250, 800)) * np.exp(-t / 0.5) * 0.25
    return stereo(np.tanh((body * 1.4 + crack * v(0.6, 0.3, 0.9) + tail) * 1.5))


def riser():
    t = t_(v(2.5, 1.8, 3.5))
    u = t / t[-1]
    noise = sweep_bp(rng.normal(0, 1, len(t)), v(200, 120, 400), v(9000, 6000, 12000), 60) * u ** 2
    f = v(110, 80, 180) * 2 ** (u * v(3, 2, 4))
    tone = sum(np.sin(2 * np.pi * np.cumsum(f * h) / SR) / h for h in (1, 2, 3)) * v(0.25, 0.1, 0.4) * u ** 1.5
    x = noise * 0.8 + tone
    x[-int(0.01 * SR):] *= np.linspace(1, 0, int(0.01 * SR))
    return stereo(x)


def glitch():
    t = t_(v(0.6, 0.4, 0.9))
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
    t = t_(v(0.12, 0.08, 0.18))
    f = v(300, 200, 500) + v(900, 500, 1500) * np.exp(-t / v(0.01, 0.006, 0.02))
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / v(0.03, 0.02, 0.05))
    return stereo(x * 0.9)


def ding():
    t = t_(v(0.9, 0.6, 1.3))
    base = v(1318.5, 880, 1760)
    ratios = [(1, 1, 0.35), (0.5, 2.0, 0.2), (0.3, 3.01, 0.12), (0.4, v(1.5, 1.25, 1.5), 0.3)]
    x = sum(a * np.sin(2 * np.pi * base * r * t) * np.exp(-t / d) for a, r, d in ratios)
    return stereo(x * 0.35)


def bass_drop():
    t = t_(v(1.6, 1.2, 2.2))
    f = v(140, 100, 220) * np.exp(-t / v(0.35, 0.2, 0.6)) + v(32, 28, 45)
    x = np.tanh(np.sin(2 * np.pi * np.cumsum(f) / SR) * v(2.2, 1.5, 3.5)) * np.minimum(1, t / 0.005) \
        * np.exp(-t / v(0.7, 0.5, 1.0))
    return stereo(x * 0.9)


def error():
    t = t_(v(0.7, 0.5, 0.9))
    f0, per = v(180, 140, 320), v(0.18, 0.12, 0.25)
    gate = ((t % per) < per * 0.72).astype(float)
    x = (np.sign(np.sin(2 * np.pi * f0 * t)) * 0.5 + np.sign(np.sin(2 * np.pi * f0 * 1.033 * t)) * 0.5) * gate
    return stereo(filt(x, "lowpass", v(2500, 1500, 4000)) * 0.4)


def click():
    t = t_(0.05)
    x = filt(rng.normal(0, 1, len(t)), "bandpass", [v(2000, 1200, 3000), v(8000, 5000, 10000)]) \
        * np.exp(-t / v(0.004, 0.002, 0.008))
    return stereo(x * 0.8)


def swell():
    x = riser()[:, 0]
    return stereo(x[::-1].copy() * np.linspace(0, 1, len(x)) ** 0.5)  # reverse-cymbal style swell


EFFECTS = [("whoosh", whoosh), ("impact", impact), ("riser", riser), ("glitch", glitch), ("pop", pop),
           ("ding", ding), ("bass-drop", bass_drop), ("error", error), ("click", click), ("swell", swell)]


def make_pack(out: Path, seed: int | None = None) -> None:
    global rng, VARY
    rng = np.random.default_rng(7 if seed is None else seed)
    VARY = seed is not None
    out.mkdir(parents=True, exist_ok=True)
    for name, fn in EFFECTS:
        x = fn()
        x = x / (np.max(np.abs(x)) + 1e-9) * 0.89  # peak about -1 dB
        with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
            sf.write(tmp.name, x, SR)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp.name, "-c:a", "pcm_s16le", str(out / f"{name}.wav")],
                           check=True)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out", nargs="?", default=str(HERE / "sfx" / "gaming"))
    ap.add_argument("--seed", type=int)
    a = ap.parse_args()
    make_pack(Path(a.out), a.seed)
    print("saved", len(EFFECTS), "effects in", a.out, "(base set)" if a.seed is None else f"(variant seed {a.seed})")


if __name__ == "__main__":
    main()
