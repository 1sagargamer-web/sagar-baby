"""Upbeat, light background music for the reaction-video channel (THE REAL SAGAR). Everything is synthesised
here (drums, bass, plucked chords, a little marimba hook), so there is no copyright or licence issue.
Separate from make_music.py (the cartoon channel's bansuri music stays as it is).

Usage:
    python3 scripts/make_music_hype.py out.wav --seconds 30 [--seed 1] [--bpm 112] [--intro]

--intro starts at full energy (no soft 2-bar lead-in), for the fast title intro.
Each seed picks a different chord loop and hook. The track ends with a short fade.
"""
import argparse
import subprocess
import tempfile

import numpy as np
import soundfile as sf

SR = 44100
LOOPS = [  # chord roots (semitones from C) and quality, 4 bars
    [(0, "M"), (7, "M"), (9, "m"), (5, "M")],
    [(9, "m"), (5, "M"), (0, "M"), (7, "M")],
    [(0, "M"), (9, "m"), (5, "M"), (7, "M")],
    [(2, "m"), (7, "M"), (0, "M"), (9, "m")],
]


def hz(semi, octave=4):
    return 261.63 * 2 ** (semi / 12 + (octave - 4))


def env(n, a, r):
    a, r = max(1, int(a * SR)), max(1, int(r * SR))
    e = np.ones(n)
    e[:a] = np.linspace(0, 1, a)
    e[-r:] *= np.linspace(1, 0, r)
    return e


def kick():
    n = int(0.35 * SR); t = np.arange(n) / SR
    f = 50 + 110 * np.exp(-t * 30)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 9)


def clap(rng):
    n = int(0.25 * SR); t = np.arange(n) / SR
    noise = rng.normal(0, 1, n)
    bursts = sum(np.exp(-np.clip(t - d, 0, None) * 60) * (t >= d) for d in (0, 0.01, 0.02))
    x = np.diff(np.concatenate([[0], noise])) * bursts * np.exp(-t * 18)
    return x * 0.5


def hat(rng, open_=False):
    n = int((0.18 if open_ else 0.05) * SR); t = np.arange(n) / SR
    x = np.diff(np.concatenate([[0], rng.normal(0, 1, n)]))
    return x * np.exp(-t * (18 if open_ else 90)) * 0.18


def pluck(f, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = sum(np.sin(2 * np.pi * f * h * t) * np.exp(-t * (6 + 3 * h)) / h for h in (1, 2, 3, 4))
    return x * env(n, 0.003, 0.05)


def marimba(f, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) * np.exp(-t * 7) + 0.3 * np.sin(2 * np.pi * f * 4 * t) * np.exp(-t * 25)
    return x * env(n, 0.002, 0.04)


def bass(f, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * f * t) + 0.25 * np.sin(2 * np.pi * f * 2 * t)
    return np.tanh(x * 1.5) * env(n, 0.005, 0.06)


def add(buf, x, at):
    s = int(at * SR)
    if s >= len(buf):
        return
    e = min(len(buf), s + len(x))
    buf[s:e] += x[: e - s]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--seconds", type=float, required=True)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--bpm", type=float, default=112)
    ap.add_argument("--intro", action="store_true")
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    total = int(a.seconds * SR)
    beat = 60 / a.bpm
    loop = LOOPS[a.seed % len(LOOPS)]
    hook = rng.choice([0, 2, 4, 7, 9, 12], size=8)
    drums, keys, low = np.zeros(total), np.zeros(total), np.zeros(total)
    k, c, h, ho = kick(), clap(rng), hat(rng), hat(rng, True)
    start_full = 0 if a.intro else 2  # bars before the drums come in
    bar = 0
    t = 0.0
    while t < a.seconds:
        root, q = loop[bar % 4]
        third = 3 if q == "m" else 4
        chord = [hz(root), hz(root + third), hz(root + 7)]
        full = bar >= start_full
        for b in range(4):
            bt = t + b * beat
            if full:
                if b in (0, 2) or (b == 3 and bar % 2):
                    add(drums, k, bt)
                if b in (1, 3):
                    add(drums, c, bt)
                for s in range(4):  # swung 16th hats
                    add(drums, (ho if s == 2 and b == 3 else h) * (0.6 if s % 2 else 1), bt + s * beat / 4 + (0.02 if s % 2 else 0))
                add(low, bass(hz(root, 2), beat * 0.9), bt)
            # off-beat plucked chords
            for f in chord:
                add(keys, pluck(f, beat * 0.45) * 0.22, bt + beat / 2)
        # marimba hook every other bar
        if full and bar % 2 == 1:
            for i, deg in enumerate(hook):
                add(keys, marimba(hz(root + deg, 5), beat * 0.4) * 0.16, t + i * beat / 2)
        t += 4 * beat
        bar += 1
    mix = drums * 0.9 + keys + low * 0.35
    fade = int(1.0 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    mix /= max(1e-9, np.max(np.abs(mix))) / 0.85
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        sf.write(tmp.name, np.stack([mix, mix], 1), SR)
        af = "aecho=0.8:0.5:40|90:0.12|0.08,highpass=f=35,loudnorm=I=-16:TP=-1.5"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp.name, "-af", af, "-ar", "48000", a.out], check=True)
    print("saved", a.out)


if __name__ == "__main__":
    main()
