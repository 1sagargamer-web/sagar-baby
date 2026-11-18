"""Tighten a person cut-out so words/emoji behind Sagar have clean edges (THE REAL SAGAR channel).

The background-removal model keeps a wide, soft fringe of the dark room around the hair and around fast-moving
hands; over bright words, smoke or emoji that fringe shows as a blurry dark halo. This keeps only the confident part
of the matte (smoothstep 0.5 -> 0.9), shrinks it by 1 px and feathers it by 0.8 px. Colours come from the footage,
so the cut-out lines up exactly with the plate underneath.

Usage:
    python3 scripts/clean_matte.py --footage assets/sagar.mp4 --matte assets/sagar-cutout.webm --out assets/sagar-clean.webm
"""
import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np
from scipy import ndimage

sys.path.insert(0, str(Path(__file__).resolve().parent))
from room_composite import frames, probe  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--footage", required=True)
    ap.add_argument("--matte", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--low", type=float, default=0.5)
    ap.add_argument("--high", type=float, default=0.9)
    a = ap.parse_args()
    w, h, fps, _ = probe(a.footage)
    rgb_cmd = ["ffmpeg", "-v", "error", "-i", a.footage, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    a_cmd = ["ffmpeg", "-v", "error", "-c:v", "libvpx-vp9", "-i", a.matte, "-vf", "alphaextract", "-f", "rawvideo",
             "-pix_fmt", "gray", "-"]
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{w}x{h}",
                            "-r", f"{fps}", "-i", "-", "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-crf", "16",
                            "-b:v", "0", "-auto-alt-ref", "0", "-row-mt", "1", a.out], stdin=subprocess.PIPE)
    n = 0
    for f, abuf in zip(frames(rgb_cmd, w * h * 3), frames(a_cmd, w * h)):
        rgb = np.frombuffer(f, np.uint8).reshape(h, w, 3)
        al = np.frombuffer(abuf, np.uint8).reshape(h, w).astype(np.float32) / 255
        t = np.clip((al - a.low) / (a.high - a.low), 0, 1)
        al = t * t * (3 - 2 * t)
        al = ndimage.gaussian_filter(ndimage.grey_erosion(al, size=(3, 3)), 0.8)
        enc.stdin.write(np.dstack([rgb, (al * 255).astype(np.uint8)]).tobytes())
        n += 1
    enc.stdin.close()
    enc.wait()
    print(f"saved {a.out} ({n} frames)")


if __name__ == "__main__":
    main()
