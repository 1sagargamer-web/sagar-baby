"""Original background music for the Bhagwan + Sagar reels: bansuri (flute) tune over a tanpura drone and a soft
keherwa tabla groove. Everything is synthesised here, so there is no copyright or licence issue.

Usage:
    python3 scripts/make_music.py out.wav --seconds 18 [--seed 3] [--bpm 96] [--key 261.63]

Each seed gives a different tune in the same style. The track ends with a short fade.
"""
import argparse
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 44100
# Bilawal / major pentatonic degrees in semitones from Sa
SCALE = [0, 2, 4, 7, 9, 12, 14, 16]


def env(n, a, d, s, r, sus_level=0.7):
    a, d, r = int(a * SR), int(d * SR), int(r * SR)
    s = max(0, n - a - d - r)
    e = np.concatenate([np.linspace(0, 1, a, endpoint=False), np.linspace(1, sus_level, d, endpoint=False),
                        np.full(s, sus_level), np.linspace(sus_level, 0, r)])
    return np.pad(e, (0, max(0, n - len(e))))[:n]


def lowpass(x, alpha):
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc += alpha * (v - acc)
        y[i] = acc
    return y


def tanpura(total, sa, rng):
    out = np.zeros(total)
    cycle = 2.6
    pattern = [(sa * 1.5 / 2, 0.0), (sa, 0.65), (sa, 1.3), (sa / 2, 1.95)]  # Pa, Sa, Sa, low Sa
    t0 = 0.0
    while t0 < total / SR:
        for f, off in pattern:
            start = int((t0 + off) * SR)
            n = min(int(3.2 * SR), total - start)
            if n <= 0:
                continue
            t = np.arange(n) / SR
            tone = np.zeros(n)
            for h in range(1, 14):  # rich "jawari" harmonics that swell then fade
                amp = (1 / h) * (1 + 0.6 * np.sin(2 * np.pi * (0.4 + 0.05 * h) * t + h))
                tone += amp * np.sin(2 * np.pi * f * h * (1 + rng.uniform(-0.0006, 0.0006)) * t)
            tone *= np.exp(-t * 0.9) * env(n, 0.01, 0.2, 0, 0.6, 0.8)
            out[start:start + n] += tone * 0.06
        t0 += cycle
    return out


def bansuri_note(f, n, rng, glide_from=None):
    t = np.arange(n) / SR
    freq = np.full(n, f)
    if glide_from:
        g = min(n, int(0.06 * SR))
        freq[:g] = np.linspace(glide_from, f, g)
    vib_depth = np.clip((t - 0.18) * 3, 0, 1) * 0.006
    freq = freq * (1 + vib_depth * np.sin(2 * np.pi * 5.2 * t))
    phase = 2 * np.pi * np.cumsum(freq) / SR
    tone = np.sin(phase) + 0.18 * np.sin(2 * phase) + 0.06 * np.sin(3 * phase)
    breath = lowpass(rng.normal(0, 1, n), 0.25) * 0.05
    return (tone + breath) * env(n, 0.05, 0.08, 0, 0.12, 0.85)


def melody(total, sa, bpm, rng):
    out = np.zeros(total)
    beat = 60 / bpm
    # short playful phrases (degree indexes into SCALE, length in beats); None = rest
    motifs = [
        [(4, 0.5), (5, 0.5), (6, 1), (5, 0.5), (4, 0.5), (3, 1)],
        [(2, 0.5), (3, 0.5), (4, 0.5), (3, 0.5), (2, 1), (0, 1)],
        [(5, 1), (4, 0.5), (3, 0.5), (4, 1.5), (None, 0.5)],
        [(3, 0.5), (4, 0.5), (5, 0.5), (7, 0.5), (6, 1), (5, 1)],
        [(4, 0.75), (3, 0.25), (2, 0.5), (1, 0.5), (0, 2)],
    ]
    order = rng.permutation(len(motifs))
    t, k, prev = beat * 2, 0, None  # tune enters after 2 beats
    while t < total / SR - beat * 2:
        motif = motifs[order[k % len(motifs)]]
        for deg, length in motif:
            n = int(length * beat * SR)
            start = int(t * SR)
            if deg is not None and start + n < total:
                f = sa * 2 ** (SCALE[deg] / 12) * 2  # one octave up: bansuri register
                out[start:start + n] += bansuri_note(f, n, rng, glide_from=prev) * 0.22
                prev = f
            t += length * beat
        t += beat * rng.choice([1, 2])  # breathing room between phrases
        k += 1
    return out


def drum(kind, rng):
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    if kind == "bayan":  # low drum with a pitch bend
        f = 85 * (1 + 0.6 * np.exp(-t * 18))
        x = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
        return x * 0.5
    if kind == "dayan":  # ringing treble drum
        f0 = 520
        x = sum(np.sin(2 * np.pi * f0 * m * t) / (i + 1) for i, m in enumerate([1, 2.0, 3.01, 4.03]))
        x = x * np.exp(-t * 14) + lowpass(rng.normal(0, 1, n), 0.2) * np.exp(-t * 60) * 0.15
        return x * 0.2
    # "na/ti": dry tap
    x = lowpass(rng.normal(0, 1, n), 0.15) * np.exp(-t * 90) * 0.6 + np.sin(2 * np.pi * 780 * t) * np.exp(-t * 45)
    return x * 0.07


def tabla(total, bpm, rng):
    out = np.zeros(total)
    step = 60 / bpm / 2  # eighth notes
    # keherwa: Dha Ge Na Ti | Na Ka Dhi Na
    pat = [("bayan", "dayan"), ("bayan",), ("tap",), ("tap",), ("tap",), ("tap",), ("bayan", "dayan"), ("tap",)]
    hits = {k: drum(k, rng) for k in ["bayan", "dayan", "tap"]}
    i, t = 0, 60 / bpm * 2
    while t < total / SR - 1.5:
        for k in pat[i % 8]:
            s = int(t * SR)
            h = hits[k] * rng.uniform(0.8, 1.0)
            e = min(total, s + len(h))
            out[s:e] += h[: e - s]
        i += 1
        t += step
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--seconds", type=float, required=True)
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--bpm", type=float, default=96)
    ap.add_argument("--key", type=float, default=261.63)  # Sa = C4
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    total = int(a.seconds * SR)
    mix = tanpura(total, a.key / 2, rng) + melody(total, a.key / 2, a.bpm, rng) + tabla(total, a.bpm, rng)
    fade = int(1.2 * SR)
    mix[-fade:] *= np.linspace(1, 0, fade)
    mix[: int(0.3 * SR)] *= np.linspace(0, 1, int(0.3 * SR))
    mix /= max(1e-9, np.max(np.abs(mix))) / 0.8
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        sf.write(tmp.name, np.stack([mix, mix], axis=1), SR)
        # soft room reverb + level to -16 LUFS (the reel lowers it under the voices)
        af = "aecho=0.8:0.7:60|130:0.25|0.15,highpass=f=60,lowpass=f=7500,loudnorm=I=-16:TP=-1.5"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp.name, "-af", af, "-ar", "48000", a.out], check=True)
    print("saved", a.out)


if __name__ == "__main__":
    main()
