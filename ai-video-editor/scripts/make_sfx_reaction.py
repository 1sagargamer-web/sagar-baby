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


def snap():
    """Crispy word pop: a sharp click, a bright blip that falls 2.4k -> 900 Hz, and a tiny low thump."""
    n = int(0.16 * SR)
    t = np.arange(n) / SR
    click = rng.normal(0, 1, n) * np.exp(-t * 900)
    click = click - onepole(click, np.full(n, 0.3))  # high-passed = crisp
    blip, _ = tone_sweep(2400, 900, 0.16, 38)
    blip = blip * np.exp(-t * 32)
    thump, _ = tone_sweep(220, 90, 0.16, 30)
    thump = thump * np.exp(-t * 35)
    x = click * 0.9 + blip * 0.7 + thump * 0.5
    return np.stack([x, x], 1)


def blip():
    n = int(0.07 * SR)
    t = np.arange(n) / SR
    b, _ = tone_sweep(2000, 1150, 0.07, 55)
    b = b * np.exp(-t * 55) + (rng.normal(0, 1, n) * np.exp(-t * 1200)) * 0.4
    return np.stack([b, b], 1)


def zip_():
    """Fast whoosh with a falling pitch (doppler) - for words flying in."""
    n = int(0.22 * SR)
    tt = np.linspace(0, 1, n)
    noise = rng.normal(0, 1, n)
    cut = 0.55 - 0.45 * tt
    air = onepole(noise, cut) - onepole(noise, cut * 0.25)
    tone, _ = tone_sweep(1700, 600, 0.22, 14)
    amp = np.sin(np.pi * np.clip(tt * 1.3, 0, 1)) ** 1.5
    x = (air * 0.8 + tone * 0.35) * amp
    return np.stack([x * (1 - 0.6 * tt), x * (0.4 + 0.6 * tt)], 1)


def burst():
    """Smoke explosion: deep boom, crackling debris, a wide air blast."""
    n = int(1.3 * SR)
    t = np.arange(n) / SR
    f = 40 + 90 * np.exp(-t * 18)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 4)
    air = onepole(rng.normal(0, 1, n), np.full(n, 0.12)) * np.exp(-t * 6) * 1.2
    crackle = np.zeros(n)
    for _ in range(70):
        s0 = int(abs(rng.normal(0.12, 0.18)) * SR)
        m = int(0.01 * SR)
        if s0 + m < n:
            crackle[s0:s0 + m] += rng.normal(0, 1, m) * np.exp(-np.arange(m) / (m / 4)) * rng.uniform(0.2, 0.8)
    crackle = crackle - onepole(crackle, np.full(n, 0.25))
    x = np.tanh((boom * 1.5 + air + crackle * 0.9) * 1.6)
    return np.stack([x, np.roll(x, 300)], 1)


def zoom_in():
    n = int(0.3 * SR)
    tt = np.linspace(0, 1, n)
    noise = rng.normal(0, 1, n)
    x = (onepole(noise, 0.03 + 0.6 * tt ** 2) - onepole(noise, 0.02 + 0.1 * tt)) * tt ** 1.6 * np.minimum(1, (1 - tt) * 12)
    return np.stack([x, x], 1)


def swipe():
    n = int(0.25 * SR)
    tt = np.linspace(0, 1, n)
    noise = rng.normal(0, 1, n)
    x = (onepole(noise, 0.15 + 0.5 * np.sin(np.pi * tt)) - onepole(noise, 0.05)) * np.sin(np.pi * tt) ** 2
    return np.stack([x, x], 1)


def sparkle():
    n = int(1.2 * SR)
    out = np.zeros((n, 2))
    notes = [1568, 1760, 2093, 2349, 2637, 3136, 3520]
    for k in range(14):
        s0 = int(k * 0.035 * SR + rng.uniform(0, 0.02) * SR)
        f = notes[rng.integers(len(notes))]
        m = n - s0
        t = np.arange(m) / SR
        b = (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 2.7 * t)) * np.exp(-t * 9) * rng.uniform(0.4, 1)
        pan = rng.uniform(0.2, 0.8)
        out[s0:, 0] += b * (1 - pan)
        out[s0:, 1] += b * pan
    return out


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
    save(snap(), out / "snap.wav", lufs=-15)
    save(blip(), out / "blip.wav", lufs=-17)
    save(zip_(), out / "zip.wav", lufs=-16)
    save(burst(), out / "burst.wav", lufs=-13)
    save(zoom_in(), out / "zoom-in.wav", lufs=-17)
    save(swipe(), out / "swipe.wav", lufs=-18)
    save(sparkle(), out / "sparkle.wav", lufs=-18)
    print("saved sfx to", out)


if __name__ == "__main__":
    main()
