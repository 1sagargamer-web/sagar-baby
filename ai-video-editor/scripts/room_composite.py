"""Put a person filmed at home into a nicer room (THE REAL SAGAR channel), so it looks real.

Usage:
    python3 scripts/room_composite.py --footage assets/sagar.mp4 --matte assets/sagar-cutout.webm \
        --bg room.jpg --person-out assets/sagar-room.webm --room-out assets/room.mp4 [--warm 4200]

--matte is the transparent WebM from `hyperframes remove-background` (only its alpha is used; colours come from
--footage). Steps:
  1. Matte clean-up: the camera is static, so the empty room is rebuilt (median of the frames where the model
     sees no person). Where the model is unsure (half-transparent patches, e.g. the chest when the hands are near
     the collar, or a smudge of wall next to the head), each pixel is compared with the empty room: different =
     person, same = room. Confident model alpha (and its soft hair edge) is kept.
  2. Person: warmed to the room's light (colour temperature), edge eroded 1 px against dark fringes, and a soft
     "light wrap" (the blurred room glowing into the edges) so the person sits in the room.
  3. Room: scaled to the footage size, slightly blurred (camera depth of field) and given moving grain like a webcam.
Outputs a transparent VP9 WebM of the person and an MP4 of the room, same length and fps as the footage.
"""
import argparse
import json
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from scipy import ndimage


def probe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate:format=duration", "-of", "json", str(path)],
                         capture_output=True, check=True, text=True).stdout
    d = json.loads(out)
    s = d["streams"][0]
    num, den = s["r_frame_rate"].split("/")
    return s["width"], s["height"], float(num) / float(den), float(d["format"]["duration"])


def frames(cmd, size):
    """Yield raw frames (bytes) from an ffmpeg command writing rawvideo to stdout."""
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    while True:
        buf = proc.stdout.read(size)
        if len(buf) < size:
            break
        yield buf
    proc.stdout.close()
    proc.wait()


def clean_plate(footage, matte, sw, sh, n_total, samples=120):
    """Median of the room where the model says 'no person' (camera is static): the empty room."""
    step = max(1, n_total // samples)
    rgb_cmd = ["ffmpeg", "-v", "error", "-i", str(footage), "-vf", f"scale={sw}:{sh}", "-f", "rawvideo",
               "-pix_fmt", "rgb24", "-"]
    a_cmd = ["ffmpeg", "-v", "error", "-c:v", "libvpx-vp9", "-i", str(matte), "-vf", f"alphaextract,scale={sw}:{sh}",
             "-f", "rawvideo", "-pix_fmt", "gray", "-"]
    stack = []
    for k, (f, a) in enumerate(zip(frames(rgb_cmd, sw * sh * 3), frames(a_cmd, sw * sh))):
        if k % step:
            continue
        img = np.frombuffer(f, np.uint8).reshape(sh, sw, 3).astype(np.float32)
        al = ndimage.binary_dilation(np.frombuffer(a, np.uint8).reshape(sh, sw) > 5, iterations=6)
        img[al] = np.nan
        stack.append(img)
    stack = np.stack(stack)
    known = np.sum(~np.isnan(stack[..., 0]), axis=0) >= 3
    plate = np.nanmedian(stack, axis=0)
    return np.nan_to_num(plate), known


def fix_matte(footage, matte, out, w, h, n_total):
    """Where the model is unsure (half-transparent, or small holes), decide person/room by comparing the frame
    with the empty-room plate. Confident model alpha is kept as it is."""
    sw, sh = w // 2, h // 2
    plate, known = clean_plate(footage, matte, sw, sh, n_total)
    rgb_cmd = ["ffmpeg", "-v", "error", "-i", str(footage), "-vf", f"scale={sw}:{sh}", "-f", "rawvideo",
               "-pix_fmt", "rgb24", "-"]
    a_cmd = ["ffmpeg", "-v", "error", "-c:v", "libvpx-vp9", "-i", str(matte), "-vf", "alphaextract", "-f", "rawvideo",
             "-pix_fmt", "gray", "-"]
    enc = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray", "-s", f"{w}x{h}",
                            "-r", "30", "-i", "-", "-c:v", "ffv1", str(out)], stdin=subprocess.PIPE)
    known_full = ndimage.zoom(known.astype(np.float32), 2, order=0)[:h, :w] > 0.5
    n, changed = 0, 0
    for f, abuf in zip(frames(rgb_cmd, sw * sh * 3), frames(a_cmd, w * h)):
        img = np.frombuffer(f, np.uint8).reshape(sh, sw, 3).astype(np.float32)
        a = np.frombuffer(abuf, np.uint8).reshape(h, w).astype(np.float32)
        diff = ndimage.gaussian_filter(np.sqrt(np.sum((img - plate) ** 2, axis=2)), 1.5)
        fg = np.clip((diff - 22) / 22, 0, 1)
        fg = ndimage.zoom(fg, 2, order=1)[:h, :w]
        unsure = (a > 8) & (a < 240)
        body = ndimage.binary_closing(a > 128, iterations=2)
        lab, nl = ndimage.label(~body)
        if nl:  # small enclosed holes inside the body are unsure too
            sizes = ndimage.sum(np.ones_like(a), lab, range(1, nl + 1))
            border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])))
            small = [i + 1 for i, sz in enumerate(sizes) if sz < 20000 and (i + 1) not in border]
            unsure |= np.isin(lab, small)
        use = unsure & known_full
        new = a.copy()
        new[use] = 255 * fg[use]
        new = ndimage.gaussian_filter(new, 0.8)
        changed += int(np.sum(np.abs(new - a) > 40))
        enc.stdin.write(np.clip(new, 0, 255).astype(np.uint8).tobytes())
        n += 1
    enc.stdin.close()
    enc.wait()
    print(f"matte: {n} frames, {changed} pixels decided by the empty-room plate")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--footage", required=True)
    ap.add_argument("--matte", required=True)
    ap.add_argument("--bg", required=True)
    ap.add_argument("--person-out", required=True)
    ap.add_argument("--room-out", required=True)
    ap.add_argument("--warm", type=int, default=4200, help="colour temperature for the person (lower = warmer)")
    ap.add_argument("--warm-mix", type=float, default=0.5)
    ap.add_argument("--room-blur", type=float, default=2.2)
    a = ap.parse_args()
    w, h, fps, dur = probe(a.footage)
    with tempfile.TemporaryDirectory() as tmp:
        alpha = Path(tmp) / "alpha.mkv"
        fix_matte(a.footage, a.matte, alpha, w, h, int(round(dur * fps)))
        fc = (
            f"[0:v]format=yuv444p,eq=gamma=1.05:contrast=1.03:saturation=1.05,format=rgb24,"
            f"colortemperature=temperature={a.warm}:mix={a.warm_mix},format=gbrp,split[g1][g2];"
            f"[1:v]format=gray,erosion,gblur=sigma=1.2,split=3[al][a2][a3];"
            f"[2:v]scale={w}:{h},gblur=sigma=30,format=gbrp,trim=duration={dur},setpts=PTS-STARTPTS[bgb];"
            f"[a2]negate,gblur=sigma=10[inv];"
            f"[a3][inv]blend=all_mode=multiply,lutyuv=y='val*1.6',format=gbrp[m];"
            f"[g1][bgb]blend=all_mode=screen[gs];"
            f"[g2][gs][m]maskedmerge,format=rgba[lw];"
            f"[lw][al]alphamerge[out]"
        )
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.footage, "-i", str(alpha), "-loop", "1", "-framerate",
                        f"{fps}", "-i", a.bg, "-filter_complex", fc, "-map", "[out]", "-t", f"{dur}",
                        "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-crf", "18", "-b:v", "0", "-auto-alt-ref", "0",
                        "-row-mt", "1", a.person_out], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-t", f"{dur}", "-framerate", f"{fps}", "-i", a.bg,
                    "-vf", f"scale={w}:{h}:flags=lanczos,gblur=sigma={a.room_blur},eq=brightness=-0.02:saturation=0.95,"
                    "noise=alls=5:allf=t,format=yuv420p", "-c:v", "libx264", "-crf", "20", "-g", f"{round(fps)}",
                    a.room_out], check=True)
    print("saved", a.person_out, a.room_out)


if __name__ == "__main__":
    main()
