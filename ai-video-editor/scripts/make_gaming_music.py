"""Original background music for the gaming channel, fully synthesised here (no copyright or licence issue).

Usage:
    python3 scripts/make_gaming_music.py out.wav --seconds 120 [--mood hype|suspense|ending] [--seed 3] [--bpm 140]

Moods:
  hype      dark trap beat: 808 bass with glides, punchy kick, clap, rolling hi-hats, minor-key pluck/bell riff.
  suspense  no drums: low drone, pulsing sub, tense detuned pad, ticking hat; for the turning point / ban reveal.
  ending    calmer: soft kick + clap, warm pad chords, slow bell melody; for the lesson / outro.
Each seed gives a different riff and drum pattern in the same style. The track loops in 8-bar phrases with small
variations (fills, drop-outs) and ends with a short fade. Output: 44.1 kHz stereo, about -18 LUFS.
The first channel's music (scripts/make_music.py) is separate and unchanged.
"""
import argparse
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, fftconvolve, sosfilt

SR = 44100
# natural minor / phrygian flavoured degrees (semitones from the root)
MINOR = [0, 2, 3, 5, 7, 8, 10, 12, 14, 15]
PHRYG = [0, 1, 3, 5, 7, 8, 10, 12, 13, 15]


def filt(x, kind, freq, order=2):
    sos = butter(order, freq, btype=kind, fs=SR, output="sos")
    return sosfilt(sos, x)


def expdec(n, tau):
    return np.exp(-np.arange(n) / (tau * SR))


def kick(rng, punch=1.0):
    n = int(0.45 * SR)
    t = np.arange(n) / SR
    f = 45 + 110 * np.exp(-t / 0.035)
    ph = 2 * np.pi * np.cumsum(f) / SR
    body = np.sin(ph) * expdec(n, 0.16)
    click = filt(rng.normal(0, 1, n), "highpass", 2500) * expdec(n, 0.004) * 0.3
    return np.tanh((body + click) * 1.6 * punch)


def clap(rng):
    n = int(0.35 * SR)
    noise = filt(rng.normal(0, 1, n), "bandpass", [900, 5000])
    env = np.zeros(n)
    for k, off in enumerate([0, 0.011, 0.023]):
        s = int(off * SR)
        env[s:] += expdec(n - s, 0.008 if k < 2 else 0.09)
    return noise * env * 0.7


def hat(rng, open_=False):
    n = int((0.25 if open_ else 0.06) * SR)
    noise = filt(rng.normal(0, 1, n), "highpass", 7000)
    return noise * expdec(n, 0.08 if open_ else 0.012) * 0.35


def sub808(freq, dur, glide_to=None):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = np.full(n, freq)
    if glide_to:
        g = int(min(0.09, dur * 0.4) * SR)
        f[-g:] = np.linspace(freq, glide_to, g)
    ph = 2 * np.pi * np.cumsum(f) / SR
    env = np.minimum(1, t / 0.004) * np.exp(-t / max(0.25, dur * 0.9))
    return np.tanh(np.sin(ph) * 1.8) * env * 0.8


def tone(freq, dur, kind="pluck", rng=None):
    n = int(dur * SR)
    t = np.arange(n) / SR
    if kind == "bell":  # FM bell / phonk-ish cowbell colour
        mod = np.sin(2 * np.pi * freq * 2.76 * t) * 2.2 * np.exp(-t / 0.25)
        x = np.sin(2 * np.pi * freq * t + mod) * np.exp(-t / 0.5)
    else:  # band-limited saw pluck
        x = sum(np.sin(2 * np.pi * freq * h * t) / h for h in range(1, 9) if freq * h < 12000)
        x = x * np.exp(-t / (0.18 if kind == "pluck" else 1.2))
        x = filt(x, "lowpass", min(9000, freq * 6))
    att = np.minimum(1, t / 0.003)
    return x * att * 0.35


def pad(freqs, dur, bright=1500):
    n = int(dur * SR)
    t = np.arange(n) / SR
    x = np.zeros(n)
    for f in freqs:
        for det in (-0.12, 0.0, 0.11):
            ff = f * 2 ** (det / 12)
            x += sum(np.sin(2 * np.pi * ff * h * t + h) / h for h in range(1, 7))
    x = filt(x, "lowpass", bright)
    env = np.minimum(1, t / 0.4) * np.minimum(1, (dur - t) / 0.4).clip(0)
    return x * env * 0.05


def reverb(x, secs=1.6, mix=0.25, rng=None):
    n = int(secs * SR)
    ir = rng.normal(0, 1, n) * expdec(n, secs / 5)
    ir = filt(ir, "lowpass", 6000)
    wet = fftconvolve(x, ir)[: len(x)]
    wet *= np.max(np.abs(x)) / (np.max(np.abs(wet)) + 1e-9)
    return x * (1 - mix) + wet * mix


def place(buf, sig, at, gain=1.0):
    s = int(at * SR)
    if s >= len(buf):
        return
    e = min(len(buf), s + len(sig))
    buf[s:e] += sig[: e - s] * gain


def build(seconds, mood, seed, bpm):
    rng = np.random.default_rng(seed)
    beat = 60 / bpm
    bar = 4 * beat
    total = int((seconds + 2) * SR)
    drums, bass, mel, padbuf = (np.zeros(total) for _ in range(4))

    root = 55.0 * 2 ** (rng.integers(0, 7) / 12)  # A1 .. E2
    scale = PHRYG if rng.random() < 0.4 else MINOR
    # 4-bar chord roots (scale degrees) and an 8-step riff per bar, chosen by the seed
    prog = [0, rng.choice([5, 3, 4]), rng.choice([3, 6, 2]), rng.choice([4, 6, 5])]
    riff = [rng.choice([None, 0, 2, 4, 7, 5, 9], p=[0.3, 0.2, 0.1, 0.15, 0.1, 0.1, 0.05]) for _ in range(16)]
    kick_pat = [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0]  # 16ths, half-time trap
    if rng.random() < 0.5:
        kick_pat[3] = 1
    voice = "bell" if rng.random() < 0.5 else "pluck"

    def note(deg, octave=0):
        return root * 2 ** ((scale[deg % len(scale)] + 12 * (deg // len(scale)) + 12 * octave) / 12)

    nbars = int(np.ceil(seconds / bar)) + 1
    for b in range(nbars):
        t0 = b * bar
        phrase = b % 8
        chord = prog[b % 4]
        drop = (phrase == 7 and rng.random() < 0.6)  # drums out on the last bar of some phrases
        intro = b < 2
        if mood == "hype":
            for k in range(16):
                at = t0 + k * beat / 4
                if kick_pat[k] and not drop and not intro:
                    place(drums, kick(rng), at, 0.9)
                if k in (4, 12) and not intro:
                    place(drums, clap(rng), at, 0.8 if not drop else 0.0)
                if k % 2 == 0 or rng.random() < 0.25:
                    place(drums, hat(rng), at, 0.55 if k % 4 else 0.8)
            if phrase in (3, 7) and not intro:  # hi-hat roll fill on the last beat
                for r in range(8):
                    place(drums, hat(rng), t0 + 3 * beat + r * beat / 8, 0.4 + r * 0.05)
            if not intro:
                nxt = note(prog[(b + 1) % 4], -1)
                place(bass, sub808(note(chord, -1), bar * 0.48), t0)
                place(bass, sub808(note(chord, -1), bar * 0.48, glide_to=nxt if rng.random() < 0.5 else None),
                      t0 + bar * 0.5)
            for k, deg in enumerate(riff):
                if deg is not None and not (drop and k > 8):
                    place(mel, tone(note(chord + deg, 2), beat * 0.6, voice), t0 + k * beat / 4)
            if phrase == 0:
                place(padbuf, pad([note(chord, 1), note(chord + 2, 1), note(chord + 4, 1)], bar * 4, 1200), t0)
        elif mood == "suspense":
            place(padbuf, pad([note(0), note(0, 1), note(1, 1) if scale is PHRYG else note(2, 1)], bar, 900), t0)
            for k in range(4):
                place(bass, sub808(note(0, -1), beat * 0.7), t0 + k * beat, 0.7)
            for k in range(8):
                place(drums, hat(rng), t0 + k * beat / 2, 0.25)
            if phrase in (3, 7):
                place(mel, tone(note(rng.choice([4, 5, 7]), 2), bar, "bell"), t0 + 2 * beat, 0.6)
        else:  # ending
            for k in range(16):
                at = t0 + k * beat / 4
                if k in (0, 10) and not intro:
                    place(drums, kick(rng, 0.7), at, 0.6)
                if k in (4, 12) and not intro:
                    place(drums, clap(rng), at, 0.5)
                if k % 2 == 0:
                    place(drums, hat(rng), at, 0.35)
            place(padbuf, pad([note(chord, 1), note(chord + 2, 1), note(chord + 4, 1)], bar, 1800), t0)
            place(bass, sub808(note(chord, -1), bar * 0.9), t0, 0.6)
            for k, deg in enumerate(riff[::2]):
                if deg is not None:
                    place(mel, tone(note(chord + deg, 2), beat * 1.5, "bell"), t0 + k * beat / 2, 0.7)

    mel = reverb(mel, 1.8, 0.3, rng)
    padbuf = reverb(padbuf, 2.5, 0.35, rng)
    mono = drums * 0.9 + bass * 0.85 + mel * 0.6 + padbuf * 0.8
    # light stereo: pad and melody slightly wide, drums and bass centred
    wide = np.roll(mel * 0.6 + padbuf * 0.8, int(0.012 * SR))
    left, right = mono + wide * 0.15, mono - wide * 0.15
    out = np.stack([left, right], 1)[: int(seconds * SR)]
    fade = int(min(2.0, seconds / 4) * SR)
    out[-fade:] *= np.linspace(1, 0, fade)[:, None]
    fin = int(0.02 * SR)
    out[:fin] *= np.linspace(0, 1, fin)[:, None]
    return np.tanh(out * 1.2)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--seconds", type=float, default=60)
    ap.add_argument("--mood", choices=["hype", "suspense", "ending"], default="hype")
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--bpm", type=float)
    a = ap.parse_args()
    # every seed also gets its own tempo (unless --bpm is given), so no two videos share the same groove
    lo, hi = {"hype": (128, 152), "suspense": (80, 100), "ending": (88, 104)}[a.mood]
    bpm = a.bpm or float(np.random.default_rng(a.seed + 1000).integers(lo, hi + 1))
    x = build(a.seconds, a.mood, a.seed, bpm)
    with tempfile.NamedTemporaryFile(suffix=".wav") as tmp:
        sf.write(tmp.name, x, SR)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp.name, "-af", "loudnorm=I=-18:TP=-1.5:LRA=11",
                        "-ar", str(SR), str(Path(a.out))], check=True)
    print("saved", a.out)


if __name__ == "__main__":
    main()
