"""Original emotional piano music (soft piano + warm strings pad), all synthesised here, so there is no copyright or
licence issue. Used by the "Uth Ja Sagar" channel (channels/uth-ja-sagar). The first channel uses make_music.py.

Usage:
    python3 scripts/make_piano.py out.wav --seconds 40 [--seed 3] [--bpm 72] [--lift 30.5] [--key 220]

--lift: time (s) where the lesson starts; the strings swell and the piano gets fuller from there.
Each seed gives a different tune and chord loop in the same style. The track ends with a gentle fade.
"""
import argparse
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 44100
# chord loops in a minor key (semitones from the tonic, 3-note chords): emotional, a little hopeful
LOOPS = [
    [[0, 3, 7], [-4, 0, 3], [-9, -5, -2], [-2, 2, 5]],  # i  VI  III  VII
    [[0, 3, 7], [-2, 2, 5], [-4, 0, 3], [-5, -1, 2]],  # i  VII VI   V
    [[-4, 0, 3], [-9, -5, -2], [-2, 2, 5], [0, 3, 7]],  # VI III VII i
    [[0, 3, 7], [5, 8, 12], [-4, 0, 3], [-2, 2, 5]],  # i  iv  VI   VII
]
MINOR = [0, 2, 3, 5, 7, 8, 10]


def hz(base, semis):
    return base * 2 ** (semis / 12)


def piano_note(f, dur, vel, rng):
    """Additive piano-ish tone: slightly stretched partials, fast attack, two-stage decay, a soft hammer click."""
    n = int((dur + 1.8) * SR)
    t = np.arange(n) / SR
    tone = np.zeros(n)
    for h in range(1, 9):
        fh = f * h * (1 + 0.0004 * h * h)  # inharmonic stretch
        if fh > 9000:
            break
        decay = 1.2 + 0.9 * h * (f / 440)
        tone += (0.9 / h ** 1.3) * np.sin(2 * np.pi * fh * t + rng.uniform(0, 6.28)) * np.exp(-t * decay)
    body = 0.65 * np.exp(-t * 2.6) + 0.35 * np.exp(-t * 0.45)
    release = np.clip((dur + 0.25 - t) / 0.25, 0, 1) ** 2 * 0.85 + 0.15 * np.exp(-np.maximum(t - dur, 0) * 4)
    att = np.clip(t / 0.006, 0, 1)
    x = tone * body * release * att
    m = min(n, 400)
    click = np.convolve(rng.normal(0, 1, m), np.ones(12) / 12, mode="same") * np.linspace(1, 0, m) ** 2 * 0.012
    x[:m] += click  # soft felt-hammer thump, low-passed so it does not click
    return x * vel


def strings(f_list, dur, rng):
    """Warm pad: detuned saw-like voices through a gentle low-pass, slow attack and release."""
    n = int((dur + 1.5) * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for f in f_list:
        for det in (-0.004, 0.0, 0.0045):
            ph = 2 * np.pi * f * (1 + det) * t + rng.uniform(0, 6.28)
            vib = 1 + 0.002 * np.sin(2 * np.pi * 5.2 * t)
            for h in range(1, 7):
                x += np.sin(ph * h * vib) / (h * 1.6)
    k = int(SR / 2500)
    x = np.convolve(x, np.ones(k) / k, mode="same")
    e = np.minimum(1, t / 0.9) * np.clip((dur + 1.2 - t) / 1.2, 0, 1)
    return x * e / (len(f_list) * 3)


def reverb(x, seconds=2.4, mix=0.32, rng=None):
    n = int(seconds * SR)
    t = np.arange(n) / SR
    ir = rng.normal(0, 1, n) * np.exp(-t * 3.0 / seconds * 2.3)
    ir[0] = 0
    k = int(SR / 4000)
    ir = np.convolve(ir, np.ones(k) / k, mode="same")
    m = len(x) + n - 1
    size = 1 << (m - 1).bit_length()
    wet = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[: len(x)]
    wet /= max(1e-9, np.max(np.abs(wet))) / max(1e-9, np.max(np.abs(x)))
    return x * (1 - mix) + wet * mix


def add(buf, sig, start):
    s = int(start * SR)
    if s >= len(buf):
        return
    e = min(len(buf), s + len(sig))
    buf[s:e] += sig[: e - s]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--seconds", type=float, required=True)
    ap.add_argument("--seed", type=int, default=3)
    ap.add_argument("--bpm", type=float, default=72)
    ap.add_argument("--lift", type=float, default=None)
    ap.add_argument("--key", type=float, default=220.0)  # tonic A3
    a = ap.parse_args()

    rng = np.random.default_rng(a.seed)
    total = a.seconds
    lift = a.lift if a.lift is not None else total * 0.72
    beat = 60 / a.bpm
    bar = beat * 4
    loop = LOOPS[a.seed % len(LOOPS)]
    base = a.key * 2 ** (rng.integers(-2, 3) / 12)  # small key change per seed
    n = int((total + 3) * SR)
    piano = np.zeros(n)
    pad = np.zeros(n)

    # melody motif per seed (scale degrees), reused with small changes so it sounds like a tune
    motif = [int(rng.integers(0, 7)) for _ in range(4)]
    t, b = 0.6, 0
    while t < total + 0.5:
        chord = loop[b % len(loop)]
        full = t >= lift
        # left hand: low root + broken chord in eighths
        root = hz(base / 2, chord[0])
        add(piano, piano_note(root, bar * 0.95, 0.5, rng), t)
        pattern = [0, 1, 2, 1, 0, 1, 2, 1]
        for i, p in enumerate(pattern):
            f = hz(base, chord[p])
            add(piano, piano_note(f, beat * 0.9, 0.22 + (0.08 if full else 0), rng), t + i * beat / 2)
        # right hand: sparse melody, two notes a bar (four after the lift), from the scale near the chord
        steps = [0, 2] if not full else [0, 1, 2, 3]
        for j, s in enumerate(steps):
            deg = (motif[(b + j) % 4] + chord[0] // 2) % 7
            octave = 12 if rng.random() < 0.8 else 24
            f = hz(base, MINOR[deg] + octave)
            if b % 4 == 3 and j == len(steps) - 1:
                f = hz(base, chord[2] + 12)  # end each loop on a chord tone
            add(piano, piano_note(f, beat * (2 if not full else 1) * 0.95, 0.42, rng), t + s * beat)
        # strings: from the second bar, soft; much fuller after the lift
        if b >= 1:
            vol = 0.35 if not full else 1.0
            add(pad, strings([hz(base / 2, c) for c in chord], bar, rng) * vol, t)
        t += bar
        b += 1

    mix = piano * 0.85 + pad * 0.55
    mix = reverb(mix, rng=rng)
    mix = mix[: int(total * SR)]
    fade = int(min(2.0, total / 4) * SR)
    mix[-fade:] *= np.linspace(1, 0, fade) ** 1.5
    mix[: int(0.05 * SR)] *= np.linspace(0, 1, int(0.05 * SR))
    stereo = np.stack([mix, np.roll(mix, int(0.012 * SR))], 1)
    stereo /= max(1e-9, np.max(np.abs(stereo))) / 0.8
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        sf.write(tmp.name, stereo, SR)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp.name, "-af", "loudnorm=I=-18:TP=-1.5", "-ar", "48000",
                        str(Path(a.out))], check=True)
    print(f"saved {a.out} ({total:.1f}s, seed {a.seed}, lift {lift:.1f}s)")


if __name__ == "__main__":
    main()
