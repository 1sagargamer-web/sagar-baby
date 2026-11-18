"""Keep Sagar's own room, but make him pop: a brighter, warmer, softly glowing person over a slightly darker room
(THE REAL SAGAR channel). Also writes the same glowing person as a transparent WebM, for words that sit behind him.

Usage:
    python3 scripts/person_glow.py --footage assets/sagar.mp4 --matte assets/sagar-cutout.webm \
        --plate-out assets/plate.mp4 --person-out assets/sagar-glow.webm [--glow 0.28] [--room-dim 0.82]

--matte: transparent WebM from `hyperframes remove-background`; it is cleaned first with the empty-room method of
room_composite.py (half-transparent chest patches filled, wall smudges removed).
"""
import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from room_composite import fix_matte, probe  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--footage", required=True)
    ap.add_argument("--matte", required=True)
    ap.add_argument("--plate-out", required=True)
    ap.add_argument("--person-out", required=True)
    ap.add_argument("--glow", type=float, default=0.28, help="strength of the soft bloom on the person")
    ap.add_argument("--room-dim", type=float, default=0.9, help="room brightness multiplier (1 = unchanged)")
    ap.add_argument("--warm", type=int, default=5200)
    a = ap.parse_args()
    w, h, fps, dur = probe(a.footage)
    with tempfile.TemporaryDirectory() as tmp:
        alpha = Path(tmp) / "alpha.mkv"
        fix_matte(a.footage, a.matte, alpha, w, h, int(round(dur * fps)))
        # The light is applied through a very soft (feathered) version of the matte, so there is never a visible
        # edge around the hair: enhanced person + soft bloom, room a little darker, then the sharp matte is used only
        # to cut the same pixels out for the front layer.
        fc = (
            f"[0:v]format=yuv444p,split[o1][o2];"
            f"[o1]eq=brightness={-(1 - a.room_dim) * 0.2:.3f}:saturation=0.96,vignette=angle=0.5,format=gbrp[room];"
            f"[o2]eq=brightness=0.035:gamma=1.10:contrast=1.04:saturation=1.10,format=rgb24,"
            f"colortemperature=temperature={a.warm}:mix=0.35,format=gbrp,split[e1][e2];"
            f"[e1]gblur=sigma=24[bl];"
            f"[e2][bl]blend=all_mode=screen:all_opacity={a.glow}[lit];"
            f"[1:v]format=gray,split[am][ac];"
            f"[am]gblur=sigma=18,format=gbrp[soft];"
            f"[room][lit][soft]maskedmerge,split[pl1][pl2];"
            f"[pl1]format=yuv420p[plate];"
            f"[ac]erosion,gblur=sigma=1.0[al];"
            f"[pl2]format=rgba[pr];[pr][al]alphamerge[person]"
        )
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a.footage, "-i", str(alpha), "-filter_complex", fc,
                        "-map", "[plate]", "-c:v", "libx264", "-crf", "15", "-g", f"{round(fps)}", a.plate_out,
                        "-map", "[person]", "-c:v", "libvpx-vp9", "-pix_fmt", "yuva420p", "-crf", "18", "-b:v", "0",
                        "-auto-alt-ref", "0", "-row-mt", "1", a.person_out], check=True)
    print("saved", a.plate_out, a.person_out)


if __name__ == "__main__":
    main()
