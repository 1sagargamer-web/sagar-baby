"""Thumbnail from a rendered reel: a frame, the in-video caption erased, big outlined text on top.

Usage: python3 scripts/make_thumb.py Export/x.mp4 out.jpg "LINE ONE" "LINE TWO" [--at 0.85]
--at = fraction of the video to take the frame from (default 0.85, near the shock/punchline).
ALWAYS look at the result before uploading (the caption erase can leave marks on busy backgrounds).
"""
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def main() -> None:
    args = [x for x in sys.argv[1:]]
    at = 0.85
    if "--at" in args:
        i = args.index("--at"); at = float(args[i + 1]); del args[i:i + 2]
    video, out, l1, l2 = args[:4]
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video],
                               capture_output=True, text=True, check=True).stdout)
    with tempfile.NamedTemporaryFile(suffix=".png") as t:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(dur * at), "-i", video, "-frames:v", "1", t.name], check=True)
        im = Image.open(t.name).convert("RGB").resize((720, 1280))
    px = im.load()
    for y in range(160, 480):                      # erase the caption box: copy each row's colour from the left edge
        c = px[20, y]
        for x in range(60, 665):
            px[x, y] = c
    d = ImageDraw.Draw(im)
    f = ImageFont.truetype(FONT, 118)
    def outlined(text, y, fill):
        size = 118
        while d.textlength(text, font=ImageFont.truetype(FONT, size)) > 650:
            size -= 6
        ff = ImageFont.truetype(FONT, size)
        x = (720 - d.textlength(text, font=ff)) / 2
        for dx in range(-6, 7, 2):
            for dy in range(-6, 7, 2):
                d.text((x + dx, y + dy), text, font=ff, fill="black")
        d.text((x, y), text, font=ff, fill=fill)
    outlined(l1, 255, "#ffe14d")
    outlined(l2, 390, "white")
    im.save(out, quality=88)
    print("saved", out)


if __name__ == "__main__":
    main()
