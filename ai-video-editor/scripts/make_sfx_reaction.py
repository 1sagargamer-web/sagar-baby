"""Sound effects for the reaction-video channel (THE REAL SAGAR), all synthesised here (no licence issues).
Separate from make_sfx.py so the cartoon channel's sounds never change.

Usage:  python3 scripts/make_sfx_reaction.py <out_dir>
Writes: pop-word.wav (bright pop for each intro word), pop-low.wav, swoosh.wav (fast air swoosh),
        impact.wav (punchy hit for bursts / punch-ins), click.wav (mouse click), bubbles.wav (many small pops,
        for the like-bubble burst), flash.wav (white-flash whoosh up), riser.wav (short build-up), ding.wav
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 48000
rng = np.random.default_rng(7)


def onepole(x, a):
    a = np.broadcast_to(a, x.shape)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += a[i] * (v - acc)
        y[i] = acc
    return y


def tone_sweep(f0, f1, dur, decay):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = f1 + (f0 - f1) * np.exp(-t * decay)
    return np.sin(2 * np.pi * np.cumsum(f) / SR), t


def pop_word():
    x, t = tone_sweep(1400, 380, 0.16, 45)
    x = x * np.exp(-t * 26)
    x += np.sin(2 * np.pi * 2600 * t) * np.exp(-t * 90) * 0.25
    x[:150] += rng.normal(0, 0.5, 150) * np.linspace(1, 0, 150)
    return np.stack([x, x], 1)


def pop_low():
    x, t = tone_sweep(700, 160, 0.2, 35)
    x = x * np.exp(-t * 20)
    return np.stack([x, x], 1)


def swoosh(dur=0.38):
    n = int(dur * SR)
    t = np.linspace(0, 1, n)
    noise = rng.normal(0, 1, n)
    cut = 0.03 + 0.5 * t ** 1.5  # opens fast -> bright
    body = onepole(noise, cut) - onepole(noise, cut * 0.2)
    amp = np.sin(np.pi * np.clip(t * 1.15, 0, 1)) ** 2
    left, right = body * amp * (1 - 0.7 * t), body * amp * (0.3 + 0.7 * t)
    return np.stack([left, right], 1)


def impact():
    n = int(0.9 * SR)
    t = np.arange(n) / SR
    f = 45 + 120 * np.exp(-t * 25)
    sub = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 5)
    crack = onepole(rng.normal(0, 1, n), np.full(n, 0.35)) * np.exp(-t * 40)
    mid = np.sin(2 * np.pi * 160 * t) * np.exp(-t * 12) * 0.4
    x = np.tanh((sub * 1.4 + crack * 1.2 + mid) * 1.8)
    return np.stack([x, x], 1)


def click():
    n = int(0.06 * SR)
    t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * 3200 * t) * np.exp(-t * 300) + rng.normal(0, 0.4, n) * np.exp(-t * 500)) * 0.8
    y = np.zeros(int(0.14 * SR))
    y[:n] += x
    y[int(0.07 * SR):int(0.07 * SR) + n] += x * 0.5  # release click
    return np.stack([y, y], 1)


def bubbles():
    n = int(1.4 * SR)
    out = np.zeros((n, 2))
    for k in range(26):
        s = int(abs(rng.normal(0.35, 0.25)) * SR)
        f0 = rng.uniform(600, 1600)
        p, t = tone_sweep(f0 * 2.2, f0, 0.09, 60)
        p = p * np.exp(-t * 40) * rng.uniform(0.4, 1.0)
        pan = rng.uniform(0.2, 0.8)
        e = min(n, s + len(p))
        out[s:e, 0] += p[: e - s] * (1 - pan)
        out[s:e, 1] += p[: e - s] * pan
    return out


def flash():
    n = int(0.55 * SR)
    t = np.linspace(0, 1, n)
    noise = rng.normal(0, 1, n)
    body = onepole(noise, 0.05 + 0.6 * t) * (t ** 1.2) * np.exp(-((t - 0.85) ** 2) * 0)
    shim = sum(np.sin(2 * np.pi * f * t * 0.55) for f in [1800, 2400, 3100]) * t ** 3 * 0.15
    x = (body + shim) * np.minimum(1, (1 - t) * 8)
    return np.stack([x, x], 1)


def riser():
    n = int(1.0 * SR)
    t = np.linspace(0, 1, n)
    f = 200 + 900 * t ** 2
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.3 + onepole(rng.normal(0, 1, n), 0.05 + 0.4 * t) * 0.7
    x *= t ** 1.5
    return np.stack([x, x], 1)


def ding():
    n = int(0.8 * SR)
    t = np.arange(n) / SR
    x = (np.sin(2 * np.pi * 1760 * t) + 0.35 * np.sin(2 * np.pi * 3520 * t)) * np.exp(-t * 5)
    return np.stack([x, x], 1)


def save(x, path, lufs=-16):
    x = x / max(1e-9, np.max(np.abs(x))) * 0.85
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        sf.write(tmp.name, x, SR)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp.name, "-af", f"loudnorm=I={lufs}:TP=-1.0",
                        "-ar", "48000", str(path)], check=True)


def main() -> None:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    save(pop_word(), out / "pop-word.wav")
    save(pop_low(), out / "pop-low.wav")
    save(swoosh(), out / "swoosh.wav")
    save(impact(), out / "impact.wav", lufs=-13)
    save(click(), out / "click.wav", lufs=-18)
    save(bubbles(), out / "bubbles.wav")
    save(flash(), out / "flash.wav")
    save(riser(), out / "riser.wav", lufs=-18)
    save(ding(), out / "ding.wav", lufs=-18)
    print("saved sfx to", out)


if __name__ == "__main__":
    main()
