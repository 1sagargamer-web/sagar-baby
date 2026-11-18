"""Tighten a person cut-out so words/emoji behind Sagar have clean edges (THE REAL SAGAR channel).

The background-removal model keeps a wide, soft fringe of the dark room around the hair and around fast-moving
hands; over bright words, smoke or emoji that fringe shows as a blurry dark halo. A hard cut fixes the halo but
makes the hair look chopped and its outline flicker frame to frame (Sagar, v4). So:
  - alpha: smoothstep(--low 0.38 -> --high 0.85), feathered 1.1 px (natural hair edge, no wide halo; 0.25/1.6 px
    left a soft dark band over bright smoke, 0.5/0.8 px looked chopped);
  - temporal smoothing: each frame's alpha is blended with its neighbours (0.25/0.5/0.25), so the outline does not
    jitter (blink) against bright smoke;
  - edge colour: half-transparent edge pixels take the colour of the nearby solid person (hair-coloured), not of
    the room behind, so there is no dark/light ring.

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
    ap.add_argument("--low", type=float, default=0.38)
    ap.add_argument("--high", type=float, default=0.85)
    ap.add_argument("--feather", type=float, default=1.1)
    a = ap.parse_args()
    w, h, fps, _ = probe(a.footage)
    rgb_cmd = ["ffmpeg", "-v", "error", "-i", a.footage, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    a_cmd = ["ffmpeg", "-v", "error", "-c:v", "libvpx-vp9", "-i", a.matte, "-vf", "alphaextract", "-f", "rawvideo",
             "-pix_fmt", "gray", "-"]
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{w}x{h}",
                            "-r", f"{fps}", "-i", "-", "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-crf", "16",
                            "-b:v", "0", "-auto-alt-ref", "0", "-row-mt", "1", a.out], stdin=subprocess.PIPE)

    def shape(al):
        t = np.clip((al - a.low) / (a.high - a.low), 0, 1)
        return t * t * (3 - 2 * t)

    def emit(rgb, al):
        al = ndimage.gaussian_filter(al, a.feather)
        core = (al > 0.97).astype(np.float32)
        den = ndimage.gaussian_filter(core, 5) + 1e-4
        rgbf = rgb.astype(np.float32)
        fg = np.stack([ndimage.gaussian_filter(rgbf[..., c] * core, 5) for c in range(3)], -1) / den[..., None]
        edge = ((al > 0.01) & (al < 0.97) & (den > 0.02))[..., None]
        out = np.where(edge, fg, rgbf)
        enc.stdin.write(np.dstack([np.clip(out, 0, 255).astype(np.uint8), (al * 255).astype(np.uint8)]).tobytes())

    prev, cur, cur_rgb, n = None, None, None, 0
    for f, abuf in zip(frames(rgb_cmd, w * h * 3), frames(a_cmd, w * h)):
        nxt = shape(np.frombuffer(abuf, np.uint8).reshape(h, w).astype(np.float32) / 255)
        nxt_rgb = np.frombuffer(f, np.uint8).reshape(h, w, 3)
        if cur is not None:
            p = prev if prev is not None else cur
            emit(cur_rgb, 0.25 * p + 0.5 * cur + 0.25 * nxt)
            n += 1
        prev, cur, cur_rgb = cur, nxt, nxt_rgb
    if cur is not None:
        emit(cur_rgb, 0.25 * (prev if prev is not None else cur) + 0.75 * cur)
        n += 1
    enc.stdin.close()
    enc.wait()
    print(f"saved {a.out} ({n} frames)")


if __name__ == "__main__":
    main()
